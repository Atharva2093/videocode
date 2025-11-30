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
    
    # CORS settings - Restrict to specific domains in production
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000"
    ]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["GET", "POST", "DELETE", "OPTIONS"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]
    
    # Download settings
    DOWNLOAD_DIR: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), "downloads")
    TEMP_DIR: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), "temp")
    MAX_CONCURRENT_DOWNLOADS: int = 3
    MAX_QUEUE_SIZE: int = 50
    
    # File size limits
    MAX_FILE_SIZE_MB: int = 2048  # 2GB max file size
    MAX_FILE_SIZE_BYTES: int = 2048 * 1024 * 1024
    
    # Video settings
    DEFAULT_FORMAT: str = "mp4"
    DEFAULT_QUALITY: str = "best"
    MAX_VIDEO_DURATION: int = 7200  # 2 hours in seconds
    ALLOW_PLAYLISTS: bool = True
    MAX_PLAYLIST_VIDEOS: int = 50
    
    # Retry settings
    MAX_RETRIES: int = 3
    RETRY_DELAY_SECONDS: int = 2
    
    # Temp file cleanup
    TEMP_FILE_MAX_AGE_HOURS: int = 24  # Delete temp files older than 24 hours
    CLEANUP_INTERVAL_MINUTES: int = 60  # Run cleanup every hour
    
    # FFmpeg settings
    FFMPEG_PATH: str = "ffmpeg"  # Use system ffmpeg by default
    
    # Rate limiting
    RATE_LIMIT_REQUESTS: int = 30  # Max requests per minute
    RATE_LIMIT_WINDOW: int = 60  # Window in seconds
    RATE_LIMIT_DOWNLOADS: int = 3  # Max downloads per minute per IP
    
    # Metadata caching
    METADATA_CACHE_TTL: int = 3600  # 1 hour in seconds
    
    # Streaming settings
    CHUNK_SIZE: int = 8192  # 8KB chunks for streaming
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


# Create global settings instance
settings = Settings()
