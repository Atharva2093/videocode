"""
YouTube Downloader API - FastAPI Backend
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
import simple_downloader
from exceptions import (
    BaseAPIError,
    InvalidURLError,
    MetadataError,
    DownloadError,
    DRMError,
    LiveStreamError,
    classify_ytdlp_error,
)
import yt_dlp
import os
import re


app = FastAPI(title="YouTube Downloader API")

# CORS - allow all origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition", "Content-Length"],
)


# ========================================
# STARTUP
# ========================================
@app.on_event("startup")
async def startup():
    print("=" * 50)
    print("YouTube Downloader API Starting...")
    
    if os.path.exists(simple_downloader.COOKIES_FILE):
        print(f"✅ Cookies: {simple_downloader.COOKIES_FILE}")
    else:
        print("⚠️  No cookies.txt found")
    
    if simple_downloader.is_ffmpeg_available():
        print("✅ FFmpeg: Available")
    else:
        print("⚠️  FFmpeg: Not found (MP3 won't work)")
    
    # Cleanup old downloads
    simple_downloader.cleanup_old_downloads(max_age_hours=1)
    print("=" * 50)


# ========================================
# EXCEPTION HANDLERS
# ========================================
@app.exception_handler(BaseAPIError)
async def handle_api_error(request: Request, exc: BaseAPIError):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.error,
            "message": exc.message,
            "hint": exc.hint,
        },
    )


@app.exception_handler(Exception)
async def handle_generic_error(request: Request, exc: Exception):
    print(f"❌ Unhandled error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "INTERNAL_ERROR",
            "message": str(exc)[:200],
            "hint": "Please try again.",
        },
    )


# ========================================
# HELPERS
# ========================================
def is_valid_youtube_url(url: str) -> bool:
    """Check if URL looks like a YouTube link."""
    if not url:
        return False
    patterns = [
        r"(https?://)?(www\.)?youtube\.com/watch\?v=[\w-]+",
        r"(https?://)?(www\.)?youtu\.be/[\w-]+",
        r"(https?://)?(www\.)?youtube\.com/shorts/[\w-]+",
        r"(https?://)?(www\.)?youtube\.com/embed/[\w-]+",
    ]
    return any(re.match(p, url) for p in patterns)


# ========================================
# ROUTES
# ========================================
@app.get("/api/health")
def health():
    """Health check endpoint."""
    return {
        "status": "ok",
        "ffmpeg": simple_downloader.is_ffmpeg_available(),
    }


@app.get("/api/metadata")
def get_metadata(url: str):
    """Fetch video metadata and available formats."""
    if not is_valid_youtube_url(url):
        raise InvalidURLError()
    
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "nocheckcertificate": True,
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
            
            # Parse formats
            video_formats = []
            audio_formats = []
            
            for f in info.get("formats", []):
                if not f.get("url"):
                    continue
                if f.get("has_drm"):
                    continue
                
                fmt = {
                    "format_id": f.get("format_id", ""),
                    "ext": f.get("ext", ""),
                    "filesize": f.get("filesize") or f.get("filesize_approx"),
                }
                
                vcodec = f.get("vcodec", "none")
                acodec = f.get("acodec", "none")
                has_video = vcodec != "none"
                has_audio = acodec != "none"
                
                if has_video:
                    fmt["height"] = f.get("height")
                    fmt["fps"] = f.get("fps")
                    fmt["has_audio"] = has_audio
                    fmt["type"] = "video"
                    video_formats.append(fmt)
                elif has_audio:
                    fmt["abr"] = f.get("abr")
                    fmt["type"] = "audio"
                    audio_formats.append(fmt)
            
            # Check for DRM if no formats found
            if not video_formats and not audio_formats:
                if any(f.get("has_drm") for f in info.get("formats", [])):
                    raise DRMError()
            
            return {
                "title": info.get("title"),
                "channel": info.get("channel") or info.get("uploader"),
                "thumbnail": info.get("thumbnail"),
                "duration": info.get("duration"),
                "video_formats": video_formats,
                "audio_formats": audio_formats,
            }
    
    except BaseAPIError:
        raise
    except Exception as e:
        raise classify_ytdlp_error(str(e))


@app.get("/api/download")
def download_video(url: str, format_id: str = "best"):
    """Download video and stream to client."""
    if not is_valid_youtube_url(url):
        raise InvalidURLError()
    
    filepath = None
    
    try:
        # Download the file
        filepath, filename = simple_downloader.download(url, format_id)
        
        if not filepath or not os.path.exists(filepath):
            raise DownloadError(
                message="Download completed but file not found.",
                hint="Try again or select a different quality.",
            )
        
        filesize = os.path.getsize(filepath)
        ext = os.path.splitext(filename)[1].lower()
        
        # Determine content type
        content_types = {
            ".mp4": "video/mp4",
            ".webm": "video/webm",
            ".mkv": "video/x-matroska",
            ".mp3": "audio/mpeg",
            ".m4a": "audio/mp4",
            ".opus": "audio/opus",
        }
        content_type = content_types.get(ext, "application/octet-stream")
        
        # Create streaming response
        def stream_file():
            nonlocal filepath
            try:
                with open(filepath, "rb") as f:
                    while True:
                        chunk = f.read(1024 * 1024)  # 1MB chunks
                        if not chunk:
                            break
                        yield chunk
            finally:
                # Cleanup after streaming
                simple_downloader.cleanup_file(filepath)
        
        return StreamingResponse(
            stream_file(),
            media_type=content_type,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Length": str(filesize),
            },
        )
    
    except BaseAPIError:
        # Cleanup on known errors
        if filepath:
            simple_downloader.cleanup_file(filepath)
        raise
    except Exception as e:
        # Cleanup on unknown errors
        if filepath:
            simple_downloader.cleanup_file(filepath)
        raise classify_ytdlp_error(str(e))
