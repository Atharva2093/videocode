"""
Simple YouTube Downloader using yt-dlp
Clean, minimal implementation for MP4 and MP3 downloads.
"""

import yt_dlp
import os
import uuid
import shutil

# ========================================
# PATHS
# ========================================
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOADS_DIR = os.path.join(BACKEND_DIR, "downloads")
COOKIES_FILE = os.path.join(BACKEND_DIR, "cookies.txt")

# Check for Render secrets path (production)
RENDER_COOKIES = "/etc/secrets/cookies.txt"
if os.path.exists(RENDER_COOKIES):
    COOKIES_FILE = RENDER_COOKIES

# Ensure downloads directory exists
os.makedirs(DOWNLOADS_DIR, exist_ok=True)


def check_ffmpeg() -> bool:
    """Check if ffmpeg is available in PATH."""
    return shutil.which("ffmpeg") is not None


def check_ffprobe() -> bool:
    """Check if ffprobe is available in PATH."""
    return shutil.which("ffprobe") is not None


def download_video(url: str, format_id: str = "best") -> str:
    """
    Download a YouTube video or audio.
    
    Args:
        url: YouTube video URL
        format_id: Either a specific format ID, "best", or "mp3"
    
    Returns:
        Full path to the downloaded file
    
    Raises:
        Exception: If download fails
    """
    # Generate unique filename
    file_id = str(uuid.uuid4())
    output_template = os.path.join(DOWNLOADS_DIR, f"{file_id}.%(ext)s")
    
    # Base options
    ydl_opts = {
        "outtmpl": output_template,
        "quiet": True,
        "no_warnings": True,
        "nocheckcertificate": True,
        "ignoreerrors": False,
        "no_color": True,
        "retries": 3,
        "fragment_retries": 3,
    }
    
    # Add cookies if available
    if os.path.exists(COOKIES_FILE):
        ydl_opts["cookiefile"] = COOKIES_FILE
    
    # Configure based on format
    if format_id == "mp3":
        # MP3 audio extraction
        ydl_opts["format"] = "bestaudio/best"
        ydl_opts["postprocessors"] = [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }]
    elif format_id and format_id != "best":
        # Specific video format - try to merge with best audio
        ydl_opts["format"] = f"{format_id}+bestaudio/{format_id}/bestvideo+bestaudio/best"
    else:
        # Best available quality
        ydl_opts["format"] = "bestvideo+bestaudio/best"
    
    # Download
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        
        if not info:
            raise Exception("Failed to extract video information")
        
        if info.get("is_live"):
            raise Exception("Live streams cannot be downloaded")
    
    # Find the downloaded file
    for filename in os.listdir(DOWNLOADS_DIR):
        if filename.startswith(file_id):
            filepath = os.path.join(DOWNLOADS_DIR, filename)
            if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
                return filepath
    
    raise Exception("Download completed but file not found")


def cleanup_old_files(max_age_hours: int = 1):
    """Remove old files from downloads directory."""
    import time
    
    now = time.time()
    max_age_seconds = max_age_hours * 3600
    
    for filename in os.listdir(DOWNLOADS_DIR):
        filepath = os.path.join(DOWNLOADS_DIR, filename)
        try:
            if os.path.isfile(filepath):
                file_age = now - os.path.getmtime(filepath)
                if file_age > max_age_seconds:
                    os.remove(filepath)
        except Exception:
            pass  # Ignore cleanup errors
