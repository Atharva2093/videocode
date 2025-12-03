# backend/main.py
import logging
import os
import re
from typing import Iterator, Optional, Tuple

from fastapi import BackgroundTasks, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

import simple_downloader
from exceptions import (
    BaseAPIError,
    DRMError,
    DownloadError,
    InvalidURLError,
    LiveStreamError,
    MetadataError,
    classify_ytdlp_error,
)

# -------------------------
# Logging
# -------------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# -------------------------
# App / Rate limiter / CORS
# -------------------------
limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="YouTube Downloader API", docs_url=None, redoc_url=None)
app.state.limiter = limiter

# Allow the frontend hosted anywhere to call API (adjust in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition", "Content-Length"],
)

# -------------------------
# Exception handlers
# -------------------------
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={
            "error": "RATE_LIMITED",
            "message": "Too many requests. Please wait.",
            "hint": "Try again in a few seconds.",
        },
    )


@app.exception_handler(BaseAPIError)
async def api_error_handler(request: Request, exc: BaseAPIError):
    # BaseAPIError should provide status_code, error, message, hint
    return JSONResponse(
        status_code=getattr(exc, "status_code", 400),
        content={
            "error": getattr(exc, "error", "API_ERROR"),
            "message": getattr(exc, "message", "An error occurred."),
            "hint": getattr(exc, "hint", ""),
        },
    )


@app.exception_handler(Exception)
async def generic_error_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error: %s", exc)
    return JSONResponse(
        status_code=500,
        content={
            "error": "INTERNAL_ERROR",
            "message": "An unexpected error occurred.",
            "hint": "Check server logs or try again.",
        },
    )


# -------------------------
# Startup info
# -------------------------
@app.on_event("startup")
async def on_startup():
    logger.info("=" * 48)
    logger.info("YouTube Downloader API Ready")
    try:
        logger.info("yt-dlp version: %s", simple_downloader.get_yt_dlp_version())
    except Exception:
        logger.info("yt-dlp version: unknown")
    try:
        logger.info("FFmpeg available: %s", simple_downloader.is_ffmpeg_available())
    except Exception:
        logger.info("FFmpeg available: unknown")
    logger.info("Cookies file path: %s", getattr(simple_downloader, "COOKIES_FILE", "not-set"))
    logger.info("=" * 48)


# -------------------------
# Helpers
# -------------------------
def is_valid_youtube_url(url: str) -> bool:
    if not url or not isinstance(url, str):
        return False
    url = url.strip()
    # strip query for matching and allow youtu.be and youtube.com/watch etc.
    base = url.split("?")[0]
    patterns = [
        r"^https?://(www\.)?youtube\.com/watch\?v=[\w-]{11}$",
        r"^https?://(www\.)?youtube\.com/shorts/[\w-]{11}$",
        r"^https?://(www\.)?youtube\.com/embed/[\w-]{11}$",
        r"^https?://(www\.)?youtu\.be/[\w-]{11}$",
    ]
    return any(re.match(p, base) for p in patterns)


# -------------------------
# Health endpoint
# -------------------------
@app.get("/api/health")
@limiter.limit("60/minute")
def health(request: Request):
    """Basic health + runtime information for debugging."""
    try:
        yt_ver = simple_downloader.get_yt_dlp_version()
    except Exception:
        yt_ver = None
    try:
        ffmpeg_ok = simple_downloader.is_ffmpeg_available()
        ffmpeg_loc = simple_downloader.get_ffmpeg_location()
    except Exception:
        ffmpeg_ok = False
        ffmpeg_loc = None

    return {
        "status": "ok",
        "yt_dlp_version": yt_ver,
        "ffmpeg_available": ffmpeg_ok,
        "ffmpeg_location": ffmpeg_loc,
    }


# -------------------------
# Metadata endpoint
# -------------------------
@app.get("/api/metadata")
@limiter.limit("30/minute")
def get_metadata(request: Request, url: str):
    """
    Fetch video metadata (title, thumbnail, duration, and downloadable mp4 formats).
    Uses a temporary cookie copy (if cookies exist) and always releases it.
    """
    if not is_valid_youtube_url(url):
        raise InvalidURLError()

    cookiefile: Optional[str] = None
    temp_cookie: Optional[str] = None
    try:
        # Acquire cookiefile (copies original into a writable temp if needed)
        cookiefile, temp_cookie = simple_downloader.acquire_cookiefile(dest_dir=None)
        ydl_opts = simple_downloader.build_metadata_opts(cookiefile)

        # run metadata extraction
        import yt_dlp  # local import to ensure classification works later
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        if not info:
            raise MetadataError()

        if info.get("is_live"):
            raise LiveStreamError()

        # simple_downloader.filter_supported_formats should exist and return only usable mp4 formats
        supported_formats = simple_downloader.filter_supported_formats(info.get("formats", []) or [])

        if not supported_formats:
            # If any format had DRM – surface a DRM error
            if any(f.get("has_drm") for f in info.get("formats", []) or []):
                raise DRMError()
            logger.error("No MP4 formats found for URL %s", url)
            raise MetadataError(hint="No downloadable MP4 formats available for this video.")

        # Build response formats (frontend expects list of format dicts)
        video_formats = []
        for entry in supported_formats:
            video_formats.append(
                {
                    "format_id": entry.get("format_id", ""),
                    "ext": entry.get("ext"),
                    "height": entry.get("height"),
                    "fps": entry.get("fps"),
                    "filesize": entry.get("filesize") or entry.get("filesize_approx"),
                    "has_audio": entry.get("acodec", "none") != "none",
                    "protocol": entry.get("protocol"),
                }
            )

        return {
            "title": info.get("title"),
            "channel": info.get("channel") or info.get("uploader"),
            "thumbnail": info.get("thumbnail"),
            "duration": info.get("duration"),
            "video_formats": video_formats,
            "ffmpeg_available": simple_downloader.is_ffmpeg_available(),
        }

    except BaseAPIError:
        # re-raise API errors so exception handler formats them
        raise
    except Exception as exc:
        logger.exception("Metadata error for url %s", url)
        # Convert yt-dlp / runtime errors to an API-friendly error
        raise classify_ytdlp_error(str(exc))
    finally:
        # Always release the temp cookie copy
        try:
            simple_downloader.release_cookiefile(temp_cookie)
        except Exception:
            logger.debug("release_cookiefile failed (ignored).")


# -------------------------
# Download endpoint (streaming)
# -------------------------
@app.get("/api/download")
@limiter.limit("10/minute")
def download_video(
    request: Request,
    background_tasks: BackgroundTasks,
    url: str,
    format_id: str = "best",
):
    """
    Prepare the download using simple_downloader.prepare_download(...)
    and stream the finished artifact to the client, while scheduling cleanup.
    """
    if not is_valid_youtube_url(url):
        raise InvalidURLError()

    # allow a safe subset of characters for format_id (prevents shell/format injection)
    if format_id and not re.match(r"^[a-zA-Z0-9_\-+]+$", format_id):
        raise InvalidURLError(message="Invalid format ID.")

    artifact = None
    cookiefile: Optional[str] = None
    temp_cookie: Optional[str] = None

    try:
        # prepare_download handles cookie usage internally (it will call acquire_cookiefile again),
        # but if your prepare_download requires cookiefile input you can adapt accordingly.
        artifact = simple_downloader.prepare_download(url, format_id)

        if not artifact or not getattr(artifact, "filepath", None) or not os.path.exists(artifact.filepath):
            raise DownloadError(message="File not found after preparation.")

        logger.info("Streaming %s (%s bytes)", artifact.filename, artifact.filesize or "unknown")

        def file_stream(path: str) -> Iterator[bytes]:
            # stream file in 1 MiB chunks
            with open(path, "rb") as fh:
                while True:
                    chunk = fh.read(1024 * 1024)
                    if not chunk:
                        break
                    yield chunk

        # sanitize filename for header (replace quotes)
        safe_filename = artifact.filename.replace('"', "'")
        headers = {
            "Content-Disposition": f'attachment; filename="{safe_filename}"',
            "Content-Type": "video/mp4",
        }
        if artifact.filesize is not None:
            headers["Content-Length"] = str(artifact.filesize)

        # schedule artifact workspace cleanup after response finishes
        background_tasks.add_task(simple_downloader.cleanup_artifact, artifact)

        return StreamingResponse(
            file_stream(artifact.filepath),
            media_type="video/mp4",
            headers=headers,
            background=background_tasks,
        )

    except BaseAPIError:
        # ensure cleanup if artifact partially created
        if artifact:
            try:
                simple_downloader.cleanup_artifact(artifact)
            except Exception:
                logger.debug("cleanup_artifact failed")
        raise
    except Exception as exc:
        # ensure cleanup on unexpected errors
        if artifact:
            try:
                simple_downloader.cleanup_artifact(artifact)
            except Exception:
                logger.debug("cleanup_artifact failed")
        logger.exception("Download error for url %s", url)
        # convert to structured API error
        raise classify_ytdlp_error(str(exc))
