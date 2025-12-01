from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from simple_downloader import download_video, get_ydl_opts
from exceptions import (
    BaseAPIError, InvalidURLError, MetadataError, DownloadError,
    DRMError, LiveStreamError, classify_ytdlp_error
)
import yt_dlp
import os
import re

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)


# ========== GLOBAL EXCEPTION HANDLER ==========
@app.exception_handler(BaseAPIError)
async def api_error_handler(request: Request, exc: BaseAPIError):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.error,
            "message": exc.message,
            "hint": exc.hint
        }
    )


@app.exception_handler(Exception)
async def generic_error_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "error": "INTERNAL_ERROR",
            "message": "An unexpected error occurred.",
            "hint": "Please try again later."
        }
    )


# ========== URL VALIDATION ==========
def validate_youtube_url(url: str) -> bool:
    """Check if URL is a valid YouTube link"""
    patterns = [
        r'(https?://)?(www\.)?youtube\.com/watch\?v=[\w-]+',
        r'(https?://)?(www\.)?youtu\.be/[\w-]+',
        r'(https?://)?(www\.)?youtube\.com/shorts/[\w-]+',
        r'(https?://)?(www\.)?youtube\.com/embed/[\w-]+',
    ]
    return any(re.match(pattern, url) for pattern in patterns)


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/metadata")
def metadata(url: str):
    # Validate URL first
    if not url or not validate_youtube_url(url):
        raise InvalidURLError()
    
    ydl_opts = get_ydl_opts()
    ydl_opts["skip_download"] = True
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            if not info:
                raise MetadataError()
            
            # Check for live streams
            if info.get("is_live"):
                raise LiveStreamError()
            
            # Filter formats that have valid URLs and are not DRM protected
            valid_formats = []
            for f in info.get("formats", []):
                # Skip formats without URLs or with DRM
                if not f.get("url"):
                    continue
                if f.get("has_drm"):
                    continue
                if f.get("vcodec") == "none":
                    continue
                    
                valid_formats.append({
                    "id": f["format_id"],
                    "ext": f.get("ext", "mp4"),
                    "quality": f.get("height"),
                    "height": f.get("height"),
                    "filesize": f.get("filesize"),
                })
            
            # Check if all formats are DRM protected
            if not valid_formats and info.get("formats"):
                has_drm = any(f.get("has_drm") for f in info.get("formats", []))
                if has_drm:
                    raise DRMError()
            
            return {
                "title": info.get("title"),
                "thumbnail": info.get("thumbnail"),
                "duration": info.get("duration"),
                "formats": valid_formats if valid_formats else [{"id": "best", "ext": "mp4", "quality": "best"}],
            }
            
    except BaseAPIError:
        # Re-raise our custom exceptions
        raise
    except Exception as e:
        error_str = str(e)
        
        # Classify the yt-dlp error and raise appropriate exception
        raise classify_ytdlp_error(error_str)


@app.get("/api/download")
def download(url: str, format_id: str = "best"):
    # Validate URL first
    if not url or not validate_youtube_url(url):
        raise InvalidURLError()
    
    try:
        filepath = download_video(url, format_id)
        if not filepath or not os.path.exists(filepath):
            raise DownloadError(
                message="Download completed but file was not created.",
                hint="Try again or select a different quality."
            )
        
        filename = os.path.basename(filepath)
        
        # Determine media type based on extension
        ext = os.path.splitext(filename)[1].lower()
        if ext == ".mp3":
            media_type = "audio/mpeg"
        elif ext == ".webm":
            media_type = "video/webm"
        else:
            media_type = "video/mp4"
        
        return FileResponse(
            filepath,
            media_type=media_type,
            filename=filename,
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
    except BaseAPIError:
        # Re-raise our custom exceptions
        raise
    except Exception as e:
        error_str = str(e)
        
        # Classify the yt-dlp error and raise appropriate exception
        raise classify_ytdlp_error(error_str)
