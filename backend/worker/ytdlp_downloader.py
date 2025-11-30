"""
Reusable yt-dlp Downloader Class
Handles metadata extraction, downloads, retries, and temp file management
"""

import os
import time
import uuid
import shutil
import asyncio
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Callable, List
from dataclasses import dataclass
from enum import Enum
import threading
import glob

import yt_dlp

from ..config import settings


class DownloadError(Exception):
    """Custom exception for download errors"""
    pass


class MetadataError(Exception):
    """Custom exception for metadata extraction errors"""
    pass


@dataclass
class VideoMetadata:
    """Video metadata structure"""
    id: str
    title: str
    description: Optional[str]
    duration: Optional[int]
    thumbnail: Optional[str]
    channel: Optional[str]
    channel_url: Optional[str]
    view_count: Optional[int]
    upload_date: Optional[str]
    filesize: Optional[int]
    filesize_approx: Optional[int]
    formats: List[Dict[str, Any]]
    is_playlist: bool = False
    playlist_count: int = 0
    
    @property
    def best_filesize(self) -> Optional[int]:
        """Get the best available filesize estimate"""
        return self.filesize or self.filesize_approx
    
    @property
    def filesize_formatted(self) -> Optional[str]:
        """Get human-readable filesize"""
        size = self.best_filesize
        if not size:
            return None
        if size >= 1073741824:
            return f"{size / 1073741824:.2f} GB"
        if size >= 1048576:
            return f"{size / 1048576:.2f} MB"
        if size >= 1024:
            return f"{size / 1024:.2f} KB"
        return f"{size} B"


class YTDLPDownloader:
    """
    Reusable yt-dlp downloader with:
    - Metadata extraction
    - Retry logic
    - Temp folder management
    - Auto cleanup of old files
    """
    
    def __init__(
        self,
        download_dir: Optional[str] = None,
        temp_dir: Optional[str] = None,
        max_retries: int = None,
        retry_delay: int = None
    ):
        self.download_dir = Path(download_dir or settings.DOWNLOAD_DIR)
        self.temp_dir = Path(temp_dir or settings.TEMP_DIR)
        self.max_retries = max_retries or settings.MAX_RETRIES
        self.retry_delay = retry_delay or settings.RETRY_DELAY_SECONDS
        
        # Ensure directories exist
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Lock for thread safety
        self._lock = threading.Lock()
        
        # Start cleanup scheduler
        self._cleanup_task = None
    
    # ============== Metadata Extraction ==============
    
    def extract_metadata(self, url: str, flat: bool = False) -> VideoMetadata:
        """
        Extract video metadata without downloading
        
        Args:
            url: YouTube URL
            flat: If True, extract playlist info without video details
            
        Returns:
            VideoMetadata object
            
        Raises:
            MetadataError: If extraction fails
        """
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': flat,
            'skip_download': True,
        }
        
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    
                    if not info:
                        raise MetadataError("No video information found")
                    
                    return self._parse_metadata(info)
                    
            except yt_dlp.utils.DownloadError as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                    continue
                    
            except Exception as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    continue
        
        raise MetadataError(f"Failed to extract metadata after {self.max_retries} attempts: {last_error}")
    
    def _parse_metadata(self, info: Dict[str, Any]) -> VideoMetadata:
        """Parse yt-dlp info dict into VideoMetadata"""
        
        # Check if playlist
        is_playlist = info.get('_type') == 'playlist' or 'entries' in info
        
        # Get filesize from best format
        filesize = None
        filesize_approx = None
        formats = []
        
        if not is_playlist:
            for fmt in info.get('formats', []):
                if fmt.get('vcodec') != 'none':
                    fmt_info = {
                        'format_id': fmt.get('format_id'),
                        'resolution': fmt.get('resolution', 'N/A'),
                        'ext': fmt.get('ext'),
                        'filesize': fmt.get('filesize'),
                        'filesize_approx': fmt.get('filesize_approx'),
                        'fps': fmt.get('fps'),
                        'vcodec': fmt.get('vcodec'),
                        'acodec': fmt.get('acodec'),
                        'tbr': fmt.get('tbr'),  # bitrate
                    }
                    formats.append(fmt_info)
                    
                    # Track best filesize estimate
                    if fmt.get('filesize'):
                        if not filesize or fmt['filesize'] > filesize:
                            filesize = fmt['filesize']
                    elif fmt.get('filesize_approx'):
                        if not filesize_approx or fmt['filesize_approx'] > filesize_approx:
                            filesize_approx = fmt['filesize_approx']
        
        return VideoMetadata(
            id=info.get('id', ''),
            title=info.get('title', 'Unknown'),
            description=info.get('description'),
            duration=info.get('duration'),
            thumbnail=info.get('thumbnail'),
            channel=info.get('uploader') or info.get('channel'),
            channel_url=info.get('uploader_url') or info.get('channel_url'),
            view_count=info.get('view_count'),
            upload_date=info.get('upload_date'),
            filesize=filesize,
            filesize_approx=filesize_approx,
            formats=formats,
            is_playlist=is_playlist,
            playlist_count=len(info.get('entries', [])) if is_playlist else 0
        )
    
    def get_filesize_estimate(self, url: str, quality: str = 'best') -> Optional[int]:
        """
        Get estimated filesize for a video
        
        Args:
            url: YouTube URL
            quality: Quality string (best, 1080p, 720p, etc.)
            
        Returns:
            Estimated filesize in bytes, or None if unavailable
        """
        try:
            metadata = self.extract_metadata(url)
            return metadata.best_filesize
        except:
            return None
    
    # ============== Download ==============
    
    def download(
        self,
        url: str,
        format: str = 'mp4',
        quality: str = 'best',
        audio_only: bool = False,
        use_temp: bool = True,
        progress_callback: Optional[Callable[[Dict], None]] = None,
        cancel_check: Optional[Callable[[], bool]] = None
    ) -> str:
        """
        Download a video with retry logic
        
        Args:
            url: YouTube URL
            format: Output format (mp4, webm, etc.)
            quality: Quality string (best, 1080p, 720p, etc.)
            audio_only: If True, extract audio only
            use_temp: If True, download to temp folder first
            progress_callback: Callback function for progress updates
            cancel_check: Callback to check if download should be cancelled
            
        Returns:
            Path to downloaded file
            
        Raises:
            DownloadError: If download fails
        """
        download_id = str(uuid.uuid4())[:8]
        
        # Determine output directory
        output_dir = self.temp_dir if use_temp else self.download_dir
        
        # Configure format
        if audio_only:
            format_spec = "bestaudio[ext=m4a]/bestaudio/best"
            ext = "mp3"
            postprocessors = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
        else:
            format_spec = self._get_format_spec(quality, format)
            ext = format
            postprocessors = []
        
        # Create progress hook
        def progress_hook(d):
            # Check for cancellation
            if cancel_check and cancel_check():
                raise DownloadError("Download cancelled by user")
            
            if progress_callback:
                progress_callback(d)
        
        # Configure yt-dlp options
        ydl_opts = {
            'format': format_spec,
            'outtmpl': str(output_dir / f'%(title)s_{download_id}.%(ext)s'),
            'progress_hooks': [progress_hook],
            'postprocessors': postprocessors,
            'quiet': True,
            'no_warnings': True,
            'ignoreerrors': False,
            'retries': self.max_retries,
            'fragment_retries': self.max_retries,
        }
        
        if format in ['mp4', 'webm']:
            ydl_opts['merge_output_format'] = format
        
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    # Extract info first
                    info = ydl.extract_info(url, download=False)
                    
                    if not info:
                        raise DownloadError("Could not extract video info")
                    
                    # Check file size limit
                    estimated_size = info.get('filesize') or info.get('filesize_approx', 0)
                    if estimated_size and estimated_size > settings.MAX_FILE_SIZE_BYTES:
                        raise DownloadError(
                            f"File too large: {estimated_size / (1024*1024):.1f}MB exceeds limit of {settings.MAX_FILE_SIZE_MB}MB"
                        )
                    
                    # Check duration limit
                    duration = info.get('duration', 0)
                    if duration and duration > settings.MAX_VIDEO_DURATION:
                        raise DownloadError(
                            f"Video too long: {duration // 60}min exceeds limit of {settings.MAX_VIDEO_DURATION // 60}min"
                        )
                    
                    # Download
                    ydl.download([url])
                    
                    # Find the downloaded file
                    title = self._sanitize_filename(info.get('title', 'video'))
                    file_pattern = str(output_dir / f'{title}_{download_id}.*')
                    matching_files = glob.glob(file_pattern)
                    
                    if not matching_files:
                        # Try broader search
                        matching_files = glob.glob(str(output_dir / f'*_{download_id}.*'))
                    
                    if not matching_files:
                        raise DownloadError("Downloaded file not found")
                    
                    downloaded_file = Path(matching_files[0])
                    
                    # Move from temp to downloads if needed
                    if use_temp:
                        final_path = self.download_dir / downloaded_file.name
                        shutil.move(str(downloaded_file), str(final_path))
                        return str(final_path)
                    
                    return str(downloaded_file)
                    
            except DownloadError:
                raise
                
            except yt_dlp.utils.DownloadError as e:
                last_error = e
                error_str = str(e).lower()
                
                # Don't retry for certain errors
                if any(err in error_str for err in ['private video', 'video unavailable', 'copyright']):
                    raise DownloadError(f"Video not available: {e}")
                
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                    continue
                    
            except Exception as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    continue
        
        raise DownloadError(f"Download failed after {self.max_retries} attempts: {last_error}")
    
    def _get_format_spec(self, quality: str, format: str) -> str:
        """Get yt-dlp format specification string"""
        quality_map = {
            '2160p': 'bestvideo[height<=2160]+bestaudio/best[height<=2160]',
            '1440p': 'bestvideo[height<=1440]+bestaudio/best[height<=1440]',
            '1080p': 'bestvideo[height<=1080]+bestaudio/best[height<=1080]',
            '720p': 'bestvideo[height<=720]+bestaudio/best[height<=720]',
            '480p': 'bestvideo[height<=480]+bestaudio/best[height<=480]',
            '360p': 'bestvideo[height<=360]+bestaudio/best[height<=360]',
            'best': 'bestvideo+bestaudio/best',
            'worst': 'worstvideo+worstaudio/worst',
        }
        return quality_map.get(quality, quality_map['best'])
    
    def _sanitize_filename(self, filename: str) -> str:
        """Remove invalid characters from filename"""
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        return filename[:100]  # Limit length
    
    # ============== Temp File Cleanup ==============
    
    def cleanup_temp_files(self, max_age_hours: Optional[int] = None) -> int:
        """
        Delete old temp files
        
        Args:
            max_age_hours: Max age in hours (default from settings)
            
        Returns:
            Number of files deleted
        """
        max_age = max_age_hours or settings.TEMP_FILE_MAX_AGE_HOURS
        cutoff_time = datetime.now() - timedelta(hours=max_age)
        deleted_count = 0
        
        with self._lock:
            try:
                for file_path in self.temp_dir.iterdir():
                    if file_path.is_file():
                        file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                        if file_mtime < cutoff_time:
                            try:
                                file_path.unlink()
                                deleted_count += 1
                            except Exception as e:
                                print(f"Failed to delete {file_path}: {e}")
            except Exception as e:
                print(f"Cleanup error: {e}")
        
        return deleted_count
    
    def cleanup_specific_file(self, file_path: str) -> bool:
        """Delete a specific file"""
        try:
            path = Path(file_path)
            if path.exists():
                path.unlink()
                return True
        except Exception as e:
            print(f"Failed to delete {file_path}: {e}")
        return False
    
    def get_temp_dir_size(self) -> int:
        """Get total size of temp directory in bytes"""
        total = 0
        try:
            for file_path in self.temp_dir.iterdir():
                if file_path.is_file():
                    total += file_path.stat().st_size
        except:
            pass
        return total
    
    async def start_cleanup_scheduler(self):
        """Start background cleanup task"""
        async def cleanup_loop():
            while True:
                await asyncio.sleep(settings.CLEANUP_INTERVAL_MINUTES * 60)
                deleted = self.cleanup_temp_files()
                if deleted > 0:
                    print(f"🧹 Cleaned up {deleted} old temp files")
        
        self._cleanup_task = asyncio.create_task(cleanup_loop())
    
    def stop_cleanup_scheduler(self):
        """Stop background cleanup task"""
        if self._cleanup_task:
            self._cleanup_task.cancel()


# Global downloader instance
downloader = YTDLPDownloader()
