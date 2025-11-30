"""
Application configuration settings
"""

from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True
    
    # CORS settings
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:8000"]
    
    # Download settings
    DOWNLOAD_DIR: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), "downloads")
    TEMP_DIR: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), "temp")
    MAX_CONCURRENT_DOWNLOADS: int = 3
    MAX_QUEUE_SIZE: int = 50
    
    # Video settings
    DEFAULT_FORMAT: str = "mp4"
    DEFAULT_QUALITY: str = "best"
    MAX_VIDEO_DURATION: int = 7200  # 2 hours in seconds
    
    # FFmpeg settings
    FFMPEG_PATH: str = "ffmpeg"  # Use system ffmpeg by default
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


# Create global settings instance
settings = Settings()
