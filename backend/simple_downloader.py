"""
Simple YouTube Downloader - Clean, Minimal Implementation
Uses yt-dlp for downloading. FFmpeg required for MP3 conversion.
"""

import yt_dlp
import os
import uuid
import shutil

# ========================================
# CONFIGURATION
# ========================================
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOADS_DIR = os.path.join(BACKEND_DIR, "downloads")
COOKIES_FILE = os.path.join(BACKEND_DIR, "cookies.txt")

# Render.com secrets path
if os.path.exists("/etc/secrets/cookies.txt"):
    COOKIES_FILE = "/etc/secrets/cookies.txt"

# Ensure downloads directory exists
os.makedirs(DOWNLOADS_DIR, exist_ok=True)


def is_ffmpeg_available() -> bool:
    """Check if ffmpeg is in PATH."""
    return shutil.which("ffmpeg") is not None


def download(url: str, format_id: str = "best") -> tuple[str, str]:
    """
    Download a YouTube video or extract audio.
    
    Args:
        url: YouTube video URL
        format_id: "best", "mp3", or a specific format ID like "137"
    
    Returns:
        Tuple of (filepath, filename)
    
    Raises:
        Exception on failure
    """
    # Generate unique file ID
    file_id = str(uuid.uuid4())
    output_template = os.path.join(DOWNLOADS_DIR, f"{file_id}.%(ext)s")
    
    # Base yt-dlp options
    ydl_opts = {
        "outtmpl": output_template,
        "quiet": True,
        "no_warnings": True,
        "nocheckcertificate": True,
        "retries": 3,
        "fragment_retries": 3,
    }
    
    # Add cookies if available
    if os.path.exists(COOKIES_FILE):
        ydl_opts["cookiefile"] = COOKIES_FILE
    
    # Configure format based on request
    if format_id == "mp3":
        # Audio extraction - requires FFmpeg
        ydl_opts["format"] = "bestaudio/best"
        ydl_opts["postprocessors"] = [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }]
    elif format_id and format_id != "best":
        # Specific format ID (e.g., "137" for 1080p)
        # Try to merge with best audio, fallback to format alone
        ydl_opts["format"] = f"{format_id}+bestaudio/{format_id}/bestvideo+bestaudio/best"
    else:
        # Best available
        ydl_opts["format"] = "bestvideo+bestaudio/best"
    
    # Download
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        if not info:
            raise Exception("Failed to extract video info")
        if info.get("is_live"):
            raise Exception("Live streams cannot be downloaded")
    
    # Find the downloaded file
    for filename in os.listdir(DOWNLOADS_DIR):
        if filename.startswith(file_id):
            filepath = os.path.join(DOWNLOADS_DIR, filename)
            if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
                return filepath, filename
    
    raise Exception("Download completed but file not found")


def cleanup_file(filepath: str):
    """Delete a file if it exists."""
    try:
        if filepath and os.path.exists(filepath):
            os.remove(filepath)
    except Exception:
        pass


def cleanup_old_downloads(max_age_hours: int = 1):
    """Remove old files from downloads directory."""
    import time
    now = time.time()
    max_age_seconds = max_age_hours * 3600
    
    try:
        for filename in os.listdir(DOWNLOADS_DIR):
            filepath = os.path.join(DOWNLOADS_DIR, filename)
            if os.path.isfile(filepath):
                age = now - os.path.getmtime(filepath)
                if age > max_age_seconds:
                    os.remove(filepath)
    except Exception:
        pass
