"""
Health check endpoints
"""

from fastapi import APIRouter
import os
import shutil

from models import HealthResponse
from config import settings

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Check the health status of the API and its dependencies
    """
    # Check yt-dlp version
    yt_dlp_version = None
    try:
        import yt_dlp
        yt_dlp_version = yt_dlp.version.__version__
    except Exception:
        pass
    
    # Check ffmpeg availability
    ffmpeg_available = shutil.which(settings.FFMPEG_PATH) is not None or shutil.which("ffmpeg") is not None
    
    # Check if download directory is writable
    download_dir_writable = False
    try:
        os.makedirs(settings.DOWNLOAD_DIR, exist_ok=True)
        test_file = os.path.join(settings.DOWNLOAD_DIR, ".write_test")
        with open(test_file, "w") as f:
            f.write("test")
        os.remove(test_file)
        download_dir_writable = True
    except Exception:
        pass
    
    return HealthResponse(
        status="healthy" if yt_dlp_version and download_dir_writable else "degraded",
        version="1.0.0",
        yt_dlp_version=yt_dlp_version,
        ffmpeg_available=ffmpeg_available,
        download_dir_writable=download_dir_writable
    )


@router.get("/ping")
async def ping():
    """Simple ping endpoint"""
    return {"ping": "pong"}
