"""
Pydantic models for request/response validation
"""

from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime


class VideoFormat(str, Enum):
    """Supported video formats"""
    MP4 = "mp4"
    WEBM = "webm"
    MKV = "mkv"
    AUDIO_ONLY = "audio"


class VideoQuality(str, Enum):
    """Supported video quality options"""
    BEST = "best"
    MEDIUM = "medium"
    WORST = "worst"
    P1080 = "1080p"
    P720 = "720p"
    P480 = "480p"
    P360 = "360p"


class DownloadStatus(str, Enum):
    """Download status states"""
    QUEUED = "queued"
    FETCHING_INFO = "fetching_info"
    DOWNLOADING = "downloading"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# Request Models
class VideoInfoRequest(BaseModel):
    """Request model for video info"""
    url: str = Field(..., description="YouTube video or playlist URL")


class DownloadRequest(BaseModel):
    """Request model for download"""
    url: str = Field(..., description="YouTube video or playlist URL")
    format: VideoFormat = Field(default=VideoFormat.MP4, description="Video format")
    quality: VideoQuality = Field(default=VideoQuality.BEST, description="Video quality")
    audio_only: bool = Field(default=False, description="Download audio only")
    playlist_items: Optional[List[int]] = Field(default=None, description="Specific playlist items to download (1-indexed)")


class CancelRequest(BaseModel):
    """Request model for cancelling a download"""
    task_id: str = Field(..., description="Task ID to cancel")


# Response Models
class FormatInfo(BaseModel):
    """Video format information"""
    format_id: str
    resolution: Optional[str] = None
    extension: str
    filesize: Optional[int] = None
    filesize_approx: Optional[int] = None
    fps: Optional[int] = None
    vcodec: Optional[str] = None
    acodec: Optional[str] = None


class VideoInfo(BaseModel):
    """Video information response"""
    id: str
    title: str
    description: Optional[str] = None
    duration: Optional[int] = None
    duration_formatted: Optional[str] = None
    thumbnail: Optional[str] = None
    channel: Optional[str] = None
    channel_url: Optional[str] = None
    view_count: Optional[int] = None
    view_count_formatted: Optional[str] = None
    upload_date: Optional[str] = None
    formats: List[FormatInfo] = []
    is_playlist: bool = False
    playlist_count: Optional[int] = None


class PlaylistInfo(BaseModel):
    """Playlist information response"""
    id: str
    title: str
    description: Optional[str] = None
    channel: Optional[str] = None
    video_count: int
    videos: List[Dict[str, Any]] = []


class DownloadProgress(BaseModel):
    """Download progress information"""
    task_id: str
    status: DownloadStatus
    title: Optional[str] = None
    progress: float = 0.0
    speed: Optional[str] = None
    eta: Optional[str] = None
    downloaded_bytes: Optional[int] = None
    total_bytes: Optional[int] = None
    error: Optional[str] = None
    file_path: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class DownloadResponse(BaseModel):
    """Response for download request"""
    task_id: str
    message: str
    status: DownloadStatus


class QueueStatus(BaseModel):
    """Download queue status"""
    active_downloads: int
    queued_downloads: int
    completed_downloads: int
    failed_downloads: int
    tasks: List[DownloadProgress] = []


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    yt_dlp_version: Optional[str] = None
    ffmpeg_available: bool
    download_dir_writable: bool
