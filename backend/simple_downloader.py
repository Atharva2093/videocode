import yt_dlp
import os
import re
import uuid
import shutil
import time
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOADS_DIR = os.path.join(BACKEND_DIR, "downloads")
COOKIES_FILE = os.path.join(BACKEND_DIR, "cookies.txt")

if os.path.exists("/etc/secrets/cookies.txt"):
    COOKIES_FILE = "/etc/secrets/cookies.txt"

os.makedirs(DOWNLOADS_DIR, exist_ok=True)


def is_ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None


def get_ffmpeg_location() -> str:
    return shutil.which("ffmpeg") or "not found"


def get_yt_dlp_version() -> str:
    return yt_dlp.version.__version__


def sanitize_title(title: str) -> str:
    if not title:
        return "video"
    safe = re.sub(r'[\\/:*?"<>|]', '', title)
    safe = re.sub(r'\s+', ' ', safe).strip()
    return safe[:150] if safe else "video"


def download(url: str, format_id: str = "best", title: str = None) -> tuple[str, str]:
    file_id = str(uuid.uuid4())
    output_template = os.path.join(DOWNLOADS_DIR, f"{file_id}.%(ext)s")
    
    ydl_opts = {
        "outtmpl": output_template,
        "quiet": True,
        "no_warnings": True,
        "nocheckcertificate": True,
        "retries": 5,
        "fragment_retries": 5,
        "socket_timeout": 30,
    }
    
    if os.path.exists(COOKIES_FILE):
        ydl_opts["cookiefile"] = COOKIES_FILE
        logger.info("Using cookies file")
    
    if is_ffmpeg_available():
        ydl_opts["ffmpeg_location"] = get_ffmpeg_location()
    
    if format_id and format_id != "best":
        ydl_opts["format"] = f"{format_id}+bestaudio/{format_id}/bestvideo+bestaudio/best"
    else:
        ydl_opts["format"] = "bestvideo+bestaudio/best"
    
    ydl_opts["merge_output_format"] = "mp4"
    
    logger.info(f"Starting download: {url[:50]}... format={format_id}")
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        if not info:
            raise Exception("Failed to extract video info")
        if info.get("is_live"):
            raise Exception("Live streams cannot be downloaded")
        
        video_title = title or info.get("title") or "video"
    
    for filename in os.listdir(DOWNLOADS_DIR):
        if filename.startswith(file_id):
            filepath = os.path.join(DOWNLOADS_DIR, filename)
            if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
                ext = os.path.splitext(filename)[1]
                safe_title = sanitize_title(video_title)
                final_name = f"{safe_title}{ext}"
                logger.info(f"Download complete: {final_name}")
                return filepath, final_name
    
    raise Exception("Download completed but file not found")


def cleanup_file(filepath: str):
    try:
        if filepath and os.path.exists(filepath):
            os.remove(filepath)
            logger.info(f"Cleaned up: {filepath}")
    except Exception as e:
        logger.warning(f"Cleanup failed: {e}")


def cleanup_old_downloads(max_age_hours: int = 1):
    now = time.time()
    max_age = max_age_hours * 3600
    count = 0
    
    try:
        for filename in os.listdir(DOWNLOADS_DIR):
            filepath = os.path.join(DOWNLOADS_DIR, filename)
            if os.path.isfile(filepath):
                if now - os.path.getmtime(filepath) > max_age:
                    os.remove(filepath)
                    count += 1
        if count:
            logger.info(f"Cleaned up {count} old files")
    except Exception as e:
        logger.warning(f"Old file cleanup failed: {e}")
