from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import simple_downloader
from exceptions import (
    BaseAPIError, InvalidURLError, MetadataError, DownloadError,
    DRMError, LiveStreamError, classify_ytdlp_error
)
import yt_dlp
import os
import re
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="YouTube Downloader API", docs_url=None, redoc_url=None)
app.state.limiter = limiter

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition", "Content-Length"],
)


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(status_code=429, content={
        "error": "RATE_LIMITED",
        "message": "Too many requests. Please wait.",
        "hint": "Try again in a few seconds."
    })


@app.exception_handler(BaseAPIError)
async def api_error_handler(request: Request, exc: BaseAPIError):
    return JSONResponse(status_code=exc.status_code, content={
        "error": exc.error,
        "message": exc.message,
        "hint": exc.hint
    })


@app.exception_handler(Exception)
async def generic_error_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {exc}")
    return JSONResponse(status_code=500, content={
        "error": "INTERNAL_ERROR",
        "message": "An unexpected error occurred.",
        "hint": "Please try again."
    })


@app.on_event("startup")
async def startup():
    logger.info("=" * 50)
    logger.info("YouTube Downloader API Starting")
    logger.info(f"yt-dlp version: {simple_downloader.get_yt_dlp_version()}")
    logger.info(f"FFmpeg: {simple_downloader.get_ffmpeg_location()}")
    logger.info(f"Cookies: {'Found' if os.path.exists(simple_downloader.COOKIES_FILE) else 'Not found'}")
    simple_downloader.cleanup_stale_workspaces(max_age_hours=6)
    logger.info("=" * 50)


def is_valid_youtube_url(url: str) -> bool:
    if not url or not isinstance(url, str):
        return False
    patterns = [
        r"^(https?://)?(www\.)?youtube\.com/watch\?v=[\w-]{11}",
        r"^(https?://)?(www\.)?youtu\.be/[\w-]{11}",
        r"^(https?://)?(www\.)?youtube\.com/shorts/[\w-]{11}",
        r"^(https?://)?(www\.)?youtube\.com/embed/[\w-]{11}",
    ]
    url = url.strip()
    return any(re.match(p, url) for p in patterns)


@app.get("/api/health")
@limiter.limit("60/minute")
def health(request: Request):
    return {
        "status": "ok",
        "yt_dlp_version": simple_downloader.get_yt_dlp_version(),
        "ffmpeg_available": simple_downloader.is_ffmpeg_available(),
        "ffmpeg_location": simple_downloader.get_ffmpeg_location()
    }


@app.get("/api/metadata")
@limiter.limit("30/minute")
def get_metadata(request: Request, url: str):
    if not is_valid_youtube_url(url):
        raise InvalidURLError()
    
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "nocheckcertificate": True,
        "socket_timeout": 15,
    }
    
    if os.path.exists(simple_downloader.COOKIES_FILE):
        ydl_opts["cookiefile"] = simple_downloader.COOKIES_FILE
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            if not info:
                raise MetadataError()
            if info.get("is_live"):
                raise LiveStreamError()
            
            video_formats = []
            for f in info.get("formats", []):
                if not f.get("url") or f.get("has_drm"):
                    continue
                
                vcodec = f.get("vcodec", "none")
                if vcodec == "none":
                    continue
                
                height = f.get("height")
                if not height:
                    continue
                
                video_formats.append({
                    "format_id": f.get("format_id", ""),
                    "ext": f.get("ext", "mp4"),
                    "height": height,
                    "fps": f.get("fps"),
                    "filesize": f.get("filesize") or f.get("filesize_approx"),
                    "has_audio": f.get("acodec", "none") != "none"
                })
            
            if not video_formats:
                if any(f.get("has_drm") for f in info.get("formats", [])):
                    raise DRMError()
                raise MetadataError(hint="No downloadable formats found.")
            
            return {
                "title": info.get("title"),
                "channel": info.get("channel") or info.get("uploader"),
                "thumbnail": info.get("thumbnail"),
                "duration": info.get("duration"),
                "video_formats": video_formats,
                "ffmpeg_available": simple_downloader.is_ffmpeg_available()
            }
    
    except BaseAPIError:
        raise
    except Exception as e:
        logger.error(f"Metadata error: {e}")
        raise classify_ytdlp_error(str(e))


@app.get("/api/download")
@limiter.limit("10/minute")
def download_video(request: Request, url: str, format_id: str = "best"):
    if not is_valid_youtube_url(url):
        raise InvalidURLError()
    
    if format_id and not re.match(r'^[a-zA-Z0-9_+-]+$', format_id):
        raise InvalidURLError(message="Invalid format ID.")
    
    artifact = None
    
    try:
        artifact = simple_downloader.prepare_download(url, format_id)

        if not artifact.filepath or not os.path.exists(artifact.filepath):
            raise DownloadError(message="File not found after preparation.")

        logger.info(
            "Streaming %s (%s bytes)",
            artifact.filename,
            artifact.filesize or "unknown"
        )

        def stream_file(path: str):
            with open(path, "rb") as file_handle:
                while chunk := file_handle.read(1024 * 1024):
                    yield chunk

        safe_filename = artifact.filename.replace('"', "'")
        headers = {
            "Content-Disposition": f'attachment; filename="{safe_filename}"',
        }
        if artifact.filesize is not None:
            headers["Content-Length"] = str(artifact.filesize)

        background = BackgroundTasks()
        background.add_task(simple_downloader.cleanup_artifact, artifact)

        return StreamingResponse(
            stream_file(artifact.filepath),
            media_type="video/mp4",
            headers=headers,
            background=background,
        )

    except BaseAPIError:
        if artifact:
            simple_downloader.cleanup_artifact(artifact)
        raise
    except Exception as e:
        if artifact:
            simple_downloader.cleanup_artifact(artifact)
        logger.error(f"Download error: {e}")
        raise classify_ytdlp_error(str(e))
