import logging
import os
import re
from typing import Iterator

import yt_dlp
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

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="YouTube Downloader API", docs_url=None, redoc_url=None)
app.state.limiter = limiter

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition", "Content-Length"],
)

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
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.error,
            "message": exc.message,
            "hint": exc.hint,
        },
    )


@app.exception_handler(Exception)
async def generic_error_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error")
    return JSONResponse(
        status_code=500,
        content={
            "error": "INTERNAL_ERROR",
            "message": "An unexpected error occurred.",
            "hint": "Please try again.",
        },
    )


@app.on_event("startup")
async def on_startup():
    logger.info("=" * 50)
    logger.info("YouTube Downloader API Ready")
    logger.info("yt-dlp version: %s", simple_downloader.get_yt_dlp_version())
    logger.info("FFmpeg location: %s", simple_downloader.get_ffmpeg_location())
    if os.path.exists(simple_downloader.COOKIES_FILE):
        logger.info("Cookies loaded from: %s", simple_downloader.COOKIES_FILE)
    else:
        logger.info("Cookies missing")
    logger.info("=" * 50)


def is_valid_youtube_url(url: str) -> bool:
    if not url or not isinstance(url, str):
        return False

    url = url.strip()
    base_url = url.split("?")[0]

    patterns = [
        r"^https?://(www\.)?youtube\.com/watch$",
        r"^https?://(www\.)?youtu\.be/[\w-]{11}$",
        r"^https?://(www\.)?youtube\.com/shorts/[\w-]{11}$",
        r"^https?://(www\.)?youtube\.com/embed/[\w-]{11}$",
    ]

    if any(re.match(pattern, base_url) for pattern in patterns):
        return True

    if "youtube.com/watch" in url and "v=" in url:
        return True

    return False


@app.get("/api/health")
@limiter.limit("60/minute")
def health(request: Request):
    return {
        "status": "ok",
        "yt_dlp_version": simple_downloader.get_yt_dlp_version(),
        "ffmpeg_available": simple_downloader.is_ffmpeg_available(),
        "ffmpeg_location": simple_downloader.get_ffmpeg_location(),
    }


@app.get("/api/metadata")
@limiter.limit("30/minute")
def get_metadata(request: Request, url: str):
    if not is_valid_youtube_url(url):
        raise InvalidURLError()

    cookiefile, temp_cookie = simple_downloader.acquire_cookiefile()
    ydl_opts = simple_downloader.build_metadata_opts(cookiefile)

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        if not info:
            raise MetadataError()
        if info.get("is_live"):
            raise LiveStreamError()

        supported_formats = simple_downloader.filter_supported_formats(info.get("formats", []))

        if not supported_formats:
            if any(f.get("has_drm") for f in info.get("formats", [])):
                raise DRMError()
            logger.error("No MP4 formats found for URL %s", url)
            raise MetadataError(hint="No downloadable MP4 formats available for this video.")

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
        raise
    except Exception as exc:
        logger.exception("Metadata error for url %s", url)
        raise classify_ytdlp_error(str(exc))
    finally:
        simple_downloader.release_cookiefile(temp_cookie)


@app.get("/api/download")
@limiter.limit("10/minute")
def download_video(
    request: Request,
    background_tasks: BackgroundTasks,
    url: str,
    format_id: str = "best",
):
    if not is_valid_youtube_url(url):
        raise InvalidURLError()

    if format_id and not re.match(r"^[a-zA-Z0-9_+-]+$", format_id):
        raise InvalidURLError(message="Invalid format ID.")

    artifact = None
    try:
        artifact = simple_downloader.prepare_download(url, format_id)
        if not artifact.filepath or not os.path.exists(artifact.filepath):
            raise DownloadError(message="File not found after preparation.")

        logger.info("Streaming %s (%s bytes)", artifact.filename, artifact.filesize or "unknown")

        def file_stream(path: str) -> Iterator[bytes]:
            with open(path, "rb") as file_handle:
                while chunk := file_handle.read(1024 * 1024):
                    yield chunk

        # Use RFC 5987 encoding for filenames with non-ASCII characters
        from urllib.parse import quote
        safe_filename = artifact.filename.replace('"', "'")
        encoded_filename = quote(safe_filename)
        headers = {
            "Content-Disposition": f'attachment; filename="{safe_filename.encode("ascii", "ignore").decode("ascii")}"; filename*=UTF-8\'\'{encoded_filename}',
            "Content-Type": "video/mp4",
        }
        if artifact.filesize is not None:
            headers["Content-Length"] = str(artifact.filesize)

        background_tasks.add_task(simple_downloader.cleanup_artifact, artifact)

        return StreamingResponse(
            file_stream(artifact.filepath),
            media_type="video/mp4",
            headers=headers,
            background=background_tasks,
        )

    except BaseAPIError:
        if artifact:
            simple_downloader.cleanup_artifact(artifact)
        raise
    except Exception as exc:
        if artifact:
            simple_downloader.cleanup_artifact(artifact)
        logger.exception("Download error for url %s", url)
        raise classify_ytdlp_error(str(exc))
