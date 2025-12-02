"""
YouTube Downloader API - FastAPI Backend
Clean, minimal implementation.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from simple_downloader import (
    download_video, 
    check_ffmpeg, 
    check_ffprobe, 
    cleanup_old_files,
    COOKIES_FILE
)
from exceptions import (
    BaseAPIError, InvalidURLError, MetadataError, DownloadError,
    DRMError, LiveStreamError, classify_ytdlp_error
)
import yt_dlp
import os
import re

app = FastAPI(title="YouTube Downloader API")

# CORS middleware
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
async def startup_event():
    """Initialize on startup."""
    if os.path.exists(COOKIES_FILE):
        print(f"🍪 Cookies loaded: {COOKIES_FILE}")
    else:
        print("⚠️ No cookies.txt found")
    
    if check_ffmpeg():
        print("✅ FFmpeg available")
    else:
        print("⚠️ FFmpeg not found - MP3 conversion won't work")
    
    # Cleanup old downloads
    cleanup_old_files(max_age_hours=1)


# ========================================
# EXCEPTION HANDLERS
# ========================================
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
    print(f"Unhandled error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "INTERNAL_ERROR",
            "message": str(exc),
            "hint": "Please try again later."
        }
    )


# ========================================
# HELPERS
# ========================================
def validate_youtube_url(url: str) -> bool:
    """Validate YouTube URL format."""
    if not url:
        return False
    patterns = [
        r'(https?://)?(www\.)?youtube\.com/watch\?v=[\w-]+',
        r'(https?://)?(www\.)?youtu\.be/[\w-]+',
        r'(https?://)?(www\.)?youtube\.com/shorts/[\w-]+',
        r'(https?://)?(www\.)?youtube\.com/embed/[\w-]+',
    ]
    return any(re.match(pattern, url) for pattern in patterns)


def sanitize_filename(name: str) -> str:
    """Remove illegal characters from filename."""
    if not name:
        return "video"
    # Remove illegal chars
    name = re.sub(r'[<>:"/\\|?*\x00-\x1F]', '', name)
    # Collapse whitespace
    name = re.sub(r'\s+', ' ', name).strip()
    # Limit length
    return name[:100] if len(name) > 100 else name


# ========================================
# ROUTES
# ========================================
@app.get("/api/health")
def health():
    """Health check endpoint."""
    return {
        "status": "ok",
        "ffmpeg": check_ffmpeg(),
        "ffprobe": check_ffprobe()
    }


@app.get("/api/metadata")
def metadata(url: str):
    """Get video metadata and available formats."""
    if not validate_youtube_url(url):
        raise InvalidURLError()
    
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "nocheckcertificate": True,
        "ignoreerrors": False,
        "no_color": True,
    }
    
    if os.path.exists(COOKIES_FILE):
        ydl_opts["cookiefile"] = COOKIES_FILE
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            if not info:
                raise MetadataError()
            
            if info.get("is_live"):
                raise LiveStreamError()
            
            # Collect formats
            video_formats = []
            audio_formats = []
            
            for f in info.get("formats", []):
                if not f.get("url") or f.get("has_drm"):
                    continue
                
                format_id = f.get("format_id", "")
                ext = f.get("ext", "unknown")
                filesize = f.get("filesize") or f.get("filesize_approx")
                vcodec = f.get("vcodec", "none")
                acodec = f.get("acodec", "none")
                height = f.get("height")
                fps = f.get("fps")
                abr = f.get("abr")
                
                has_video = vcodec != "none"
                has_audio = acodec != "none"
                
                if has_video:
                    video_formats.append({
                        "format_id": format_id,
                        "ext": ext,
                        "filesize": filesize,
                        "height": height,
                        "fps": fps,
                        "has_audio": has_audio,
                        "type": "video"
                    })
                elif has_audio:
                    audio_formats.append({
                        "format_id": format_id,
                        "ext": ext,
                        "filesize": filesize,
                        "abr": abr,
                        "type": "audio"
                    })
            
            # Check for DRM
            if not video_formats and not audio_formats:
                has_drm = any(f.get("has_drm") for f in info.get("formats", []))
                if has_drm:
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
def download(url: str, format_id: str = "best"):
    """Download video/audio and stream to client."""
    if not validate_youtube_url(url):
        raise InvalidURLError()
    
    try:
        # Download the file
        filepath = download_video(url, format_id)
        
        if not filepath or not os.path.exists(filepath):
            raise DownloadError(
                message="Download completed but file was not created.",
                hint="Try again or select a different quality."
            )
        
        # Get file info
        filename = os.path.basename(filepath)
        filesize = os.path.getsize(filepath)
        ext = os.path.splitext(filename)[1].lower()
        
        # Determine content type
        if ext == ".mp3":
            content_type = "audio/mpeg"
        elif ext == ".webm":
            content_type = "video/webm"
        elif ext == ".m4a":
            content_type = "audio/mp4"
        else:
            content_type = "video/mp4"
        
        # Stream the file
        def file_iterator():
            try:
                with open(filepath, "rb") as f:
                    while chunk := f.read(1024 * 1024):  # 1MB chunks
                        yield chunk
            finally:
                # Clean up file after streaming
                try:
                    os.remove(filepath)
                except Exception:
                    pass
        
        return StreamingResponse(
            file_iterator(),
            media_type=content_type,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Length": str(filesize),
            }
        )
        
    except BaseAPIError:
        raise
    except Exception as e:
        raise classify_ytdlp_error(str(e))
