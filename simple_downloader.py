"""
YouTube Downloader - Core Helper Functions
Optimized for maximum download speed with aria2c support
"""

import os
import re
import shutil
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Windows compatibility for yt-dlp
if sys.platform == "win32":
    import types
    termios_mock = types.ModuleType("termios")
    sys.modules["termios"] = termios_mock
    tty_mock = types.ModuleType("tty")
    sys.modules["tty"] = tty_mock

try:
    import yt_dlp
except ImportError:
    print("ERROR: yt-dlp is not installed")
    print("Install it with: pip install yt-dlp")
    sys.exit(1)

from exceptions import (
    InvalidURLError,
    NoMP4FormatsError,
    DRMProtectedError,
    VideoUnavailableError,
    NetworkError,
)


def is_aria2c_available() -> bool:
    """
    Check if aria2c is installed and available in PATH
    
    Returns:
        True if aria2c is available, False otherwise
    """
    return shutil.which("aria2c") is not None


def sanitize_filename(title: str) -> str:
    """
    Sanitize video title for safe filename usage
    
    Args:
        title: Video title string
        
    Returns:
        Safe filename string (max 200 chars)
    """
    if not title:
        return "video"
    
    # Remove invalid filename characters for Windows/Linux/Mac
    sanitized = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '', title)
    
    # Remove leading/trailing spaces and dots
    sanitized = sanitized.strip('. ')
    
    # Replace multiple spaces with single space
    sanitized = re.sub(r'\s+', ' ', sanitized)
    
    # Limit length to avoid filesystem issues
    if len(sanitized) > 200:
        sanitized = sanitized[:200].strip()
    
    return sanitized if sanitized else "video"


def validate_youtube_url(url: str) -> bool:
    """
    Validate if URL is a supported YouTube URL
    
    Args:
        url: URL to validate
        
    Returns:
        True if valid YouTube URL
    """
    youtube_patterns = [
        r'(https?://)?(www\.)?youtube\.com/watch\?v=[\w-]+',
        r'(https?://)?(www\.)?youtu\.be/[\w-]+',
        r'(https?://)?(www\.)?youtube\.com/shorts/[\w-]+',
        r'(https?://)?(www\.)?youtube\.com/embed/[\w-]+',
    ]
    
    return any(re.match(pattern, url) for pattern in youtube_patterns)


def get_mp4_formats(url: str) -> Tuple[str, int, List[Dict]]:
    """
    Extract video metadata and available MP4 formats
    
    Args:
        url: YouTube video URL
        
    Returns:
        Tuple of (title, duration, list of MP4 formats)
        
    Raises:
        InvalidURLError: If URL is invalid
        NoMP4FormatsError: If no MP4 formats available
        VideoUnavailableError: If video is unavailable
        DRMProtectedError: If video is DRM protected
    """
    if not validate_youtube_url(url):
        raise InvalidURLError("Invalid YouTube URL format")
    
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
        'skip_download': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            if not info:
                raise VideoUnavailableError("Could not fetch video information")
            
            title = info.get('title', 'Unknown Video')
            duration = info.get('duration', 0)
            
            # Check for DRM
            if info.get('is_drm_protected'):
                raise DRMProtectedError("Video is DRM-protected and cannot be downloaded")
            
            # Filter MP4 formats
            formats = info.get('formats', [])
            mp4_formats = []
            
            for fmt in formats:
                # Only keep MP4 video formats with both video and audio or video-only
                if (fmt.get('ext') == 'mp4' and 
                    fmt.get('vcodec') != 'none' and 
                    fmt.get('height')):
                    
                    mp4_formats.append({
                        'format_id': fmt['format_id'],
                        'height': fmt['height'],
                        'fps': fmt.get('fps', 30),
                        'filesize': fmt.get('filesize') or fmt.get('filesize_approx', 0),
                        'has_audio': fmt.get('acodec') != 'none',
                    })
            
            if not mp4_formats:
                raise NoMP4FormatsError("No MP4 formats available for this video")
            
            # Sort by height (quality) descending
            mp4_formats.sort(key=lambda x: (x['height'], x['fps']), reverse=True)
            
            # Remove duplicate heights, keep highest fps
            seen_heights = set()
            unique_formats = []
            for fmt in mp4_formats:
                if fmt['height'] not in seen_heights:
                    unique_formats.append(fmt)
                    seen_heights.add(fmt['height'])
            
            return title, duration, unique_formats
            
    except yt_dlp.utils.DownloadError as e:
        error_msg = str(e).lower()
        
        if 'drm' in error_msg:
            raise DRMProtectedError("Video is DRM-protected and cannot be downloaded")
        elif 'private' in error_msg or 'unavailable' in error_msg:
            raise VideoUnavailableError("Video is unavailable or removed")
        elif 'copyright' in error_msg:
            raise VideoUnavailableError("Video removed due to copyright")
        elif 'live' in error_msg:
            raise VideoUnavailableError("Live streams are not supported")
        else:
            raise NetworkError(f"Network error: {e}")
            
    except Exception as e:
        raise NetworkError(f"Unexpected error: {e}")


def get_download_options(format_id: Optional[str], output_path: str, use_aria2c: bool) -> Dict:
    """
    Prepare optimized yt-dlp download options
    
    Args:
        format_id: Specific format ID or None for best
        output_path: Full path including filename template
        use_aria2c: Whether to use aria2c external downloader
        
    Returns:
        Dictionary of yt-dlp options optimized for speed
    """
    # Base options for maximum speed
    options = {
        'format': format_id if format_id else 'best[ext=mp4]',
        'outtmpl': output_path,
        'quiet': False,
        'no_warnings': False,
        
        # High-performance settings
        'concurrent_fragment_downloads': 16,
        'retries': 20,
        'fragment_retries': 20,
        'file_access_retries': 10,
        'http_chunk_size': 10485760,  # 10MB
        'throttledratelimit': 0,  # No rate limiting
        'socket_timeout': 30,
        
        # Progress display
        'progress_hooks': [_progress_hook],
        'noprogress': False,
    }
    
    # Use aria2c if available for massive speed boost
    if use_aria2c:
        options['external_downloader'] = 'aria2c'
        options['external_downloader_args'] = [
            '--max-connection-per-server=16',
            '--split=16',
            '--min-split-size=1M',
            '--max-tries=20',
            '--retry-wait=3',
            '--timeout=30',
            '--connect-timeout=30',
        ]
    
    return options


def download_video(url: str, download_folder: str, format_id: Optional[str] = None) -> str:
    """
    Download YouTube video with maximum speed optimization
    
    Args:
        url: YouTube video URL
        download_folder: Directory to save video
        format_id: Specific format ID or None for best quality
        
    Returns:
        Path to downloaded file
        
    Raises:
        Various exceptions for different error conditions
    """
    # Create download folder if it doesn't exist
    folder_path = Path(download_folder)
    folder_path.mkdir(parents=True, exist_ok=True)
    
    # Get video info first
    title, _, _ = get_mp4_formats(url)
    safe_title = sanitize_filename(title)
    
    # Prepare output template
    output_template = str(folder_path / f"{safe_title}.mp4")
    
    # Check aria2c availability
    use_aria2c = is_aria2c_available()
    
    if use_aria2c:
        print("\n[SPEED BOOST] Using aria2c (16 parallel connections)")
    else:
        print("\n[INFO] aria2c not found - using high-performance yt-dlp mode")
        print("[TIP] Install aria2c for 5-15x faster downloads!")
    
    # Get optimized download options
    ydl_opts = get_download_options(format_id, output_template, use_aria2c)
    
    print(f"\n[DOWNLOADING] {safe_title}")
    print(f"[SAVING TO] {download_folder}\n")
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
            
        # Find the downloaded file
        downloaded_file = Path(output_template)
        
        if not downloaded_file.exists():
            # Try with different extensions
            for ext in ['.mp4', '.mkv', '.webm']:
                alt_file = folder_path / f"{safe_title}{ext}"
                if alt_file.exists():
                    downloaded_file = alt_file
                    break
        
        if not downloaded_file.exists():
            raise FileNotFoundError("Download completed but file not found")
        
        return str(downloaded_file)
        
    except KeyboardInterrupt:
        print("\n\n[CANCELLED] Download cancelled by user")
        raise
    except Exception as e:
        error_msg = str(e).lower()
        
        if 'http error 403' in error_msg or 'forbidden' in error_msg:
            raise VideoUnavailableError("Access forbidden - video may be region-locked")
        elif 'http error 404' in error_msg:
            raise VideoUnavailableError("Video not found (removed or deleted)")
        elif 'timeout' in error_msg or 'timed out' in error_msg:
            raise NetworkError("Network timeout - connection too slow, try again")
        else:
            raise NetworkError(f"Download failed: {e}")


def _progress_hook(d):
    """Internal progress callback for yt-dlp"""
    if d['status'] == 'downloading':
        total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
        downloaded = d.get('downloaded_bytes', 0)
        speed = d.get('speed')
        eta = d.get('eta')
        
        if total > 0 and downloaded > 0:
            percent = (downloaded / total) * 100
            speed_mb = (speed / (1024 * 1024)) if speed else 0
            eta_val = int(eta) if eta else 0
            
            print(f"\rProgress: {percent:6.2f}% | Speed: {speed_mb:6.2f} MB/s | ETA: {eta_val:3d}s", 
                  end='', flush=True)
        elif downloaded > 0:
            # Show progress even without total
            speed_mb = (speed / (1024 * 1024)) if speed else 0
            downloaded_mb = downloaded / (1024 * 1024)
            print(f"\rDownloaded: {downloaded_mb:6.2f} MB | Speed: {speed_mb:6.2f} MB/s", 
                  end='', flush=True)
    
    elif d['status'] == 'finished':
        print("\n[PROCESSING] Finalizing download...", flush=True)
