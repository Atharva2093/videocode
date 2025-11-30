"""
Download endpoints - Phase 2
Includes: /download (queue-based), /download/direct, /convert, /mobile-compression
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, StreamingResponse
import os
import tempfile
import uuid
import asyncio
import yt_dlp
import subprocess
import shutil
from pathlib import Path

from ..models import (
    DownloadRequest, DownloadResponse, DownloadProgress,
    QueueStatus, CancelRequest, DownloadStatus,
    DirectDownloadRequest, ConvertRequest, MobileCompressionRequest, AudioQuality
)
from ..worker import download_manager
from ..config import settings

router = APIRouter()


# ============== Helper Functions ==============

def get_temp_dir():
    """Get or create temp directory for downloads"""
    temp_dir = Path(tempfile.gettempdir()) / "videocode_downloads"
    temp_dir.mkdir(exist_ok=True)
    return temp_dir


def sanitize_filename(filename: str) -> str:
    """Remove invalid characters from filename"""
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename[:200]  # Limit length


def get_quality_format(quality: str, audio_only: bool = False) -> str:
    """Get yt-dlp format string based on quality"""
    if audio_only:
        return 'bestaudio[ext=m4a]/bestaudio/best'
    
    quality_map = {
        '2160p': 'bestvideo[height<=2160]+bestaudio/best[height<=2160]',
        '1440p': 'bestvideo[height<=1440]+bestaudio/best[height<=1440]',
        '1080p': 'bestvideo[height<=1080]+bestaudio/best[height<=1080]',
        '720p': 'bestvideo[height<=720]+bestaudio/best[height<=720]',
        '480p': 'bestvideo[height<=480]+bestaudio/best[height<=480]',
        '360p': 'bestvideo[height<=360]+bestaudio/best[height<=360]',
        'best': 'bestvideo+bestaudio/best',
    }
    return quality_map.get(quality, quality_map['best'])


# ============== Queue-Based Download Endpoints ==============

@router.post("/download", response_model=DownloadResponse)
async def start_download(request: DownloadRequest):
    """
    POST /download - Queue-based download (async)
    
    Adds download to queue and returns task_id for tracking.
    Use GET /download/{task_id} to check status.
    """
    try:
        task_id = await download_manager.add_download(
            url=request.url,
            format=request.format.value,
            quality=request.quality.value,
            audio_only=request.audio_only,
            playlist_items=request.playlist_items
        )
        
        return DownloadResponse(
            task_id=task_id,
            message="Download queued successfully",
            status=DownloadStatus.QUEUED
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to queue download: {str(e)}")


@router.get("/download/{task_id}", response_model=DownloadProgress)
async def get_download_status(task_id: str):
    """
    GET /download/{task_id} - Get status of queued download
    """
    task = download_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.post("/download/cancel")
async def cancel_download(request: CancelRequest):
    """
    POST /download/cancel - Cancel a queued download
    """
    success = await download_manager.cancel_download(request.task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found or already completed")
    return {"message": "Download cancelled", "task_id": request.task_id}


@router.delete("/download/{task_id}")
async def remove_download(task_id: str):
    """
    DELETE /download/{task_id} - Remove download from history
    """
    success = download_manager.remove_task(task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"message": "Task removed", "task_id": task_id}


@router.get("/queue", response_model=QueueStatus)
async def get_queue_status():
    """
    GET /queue - Get current download queue status
    """
    return download_manager.get_queue_status()


@router.get("/download/{task_id}/file")
async def download_file(task_id: str):
    """
    GET /download/{task_id}/file - Download completed file
    """
    task = download_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task.status != DownloadStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Download not completed yet")
    
    if not task.file_path or not os.path.exists(task.file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    filename = os.path.basename(task.file_path)
    return FileResponse(
        path=task.file_path,
        filename=filename,
        media_type='application/octet-stream'
    )


@router.delete("/queue/clear")
async def clear_completed():
    """
    DELETE /queue/clear - Clear completed/failed downloads
    """
    count = download_manager.clear_completed()
    return {"message": f"Cleared {count} tasks"}


# ============== Direct Download Endpoint ==============

@router.post("/download/direct")
async def direct_download(request: DirectDownloadRequest):
    """
    POST /download/direct - Synchronous download returning file directly
    
    Downloads video/audio and returns the file as a downloadable response.
    Best for small files or when immediate download is needed.
    
    WARNING: This blocks until download is complete. For large files,
    use the queue-based /download endpoint instead.
    """
    try:
        temp_dir = get_temp_dir()
        download_id = str(uuid.uuid4())[:8]
        
        # Get video info first for filename
        ydl_opts_info = {'quiet': True, 'no_warnings': True}
        with yt_dlp.YoutubeDL(ydl_opts_info) as ydl:
            info = ydl.extract_info(request.url, download=False)
        
        title = sanitize_filename(info.get('title', 'video'))
        ext = 'mp3' if request.audio_only else request.format
        output_path = temp_dir / f"{title}_{download_id}.{ext}"
        
        # Configure download options
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'outtmpl': str(temp_dir / f"{title}_{download_id}.%(ext)s"),
        }
        
        if request.audio_only:
            ydl_opts['format'] = 'bestaudio[ext=m4a]/bestaudio/best'
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
            output_path = temp_dir / f"{title}_{download_id}.mp3"
        else:
            ydl_opts['format'] = get_quality_format(request.quality)
            if request.format == 'mp4':
                ydl_opts['merge_output_format'] = 'mp4'
        
        # Perform download
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([request.url])
        
        # Find the downloaded file
        if not output_path.exists():
            # Search for file with matching pattern
            for f in temp_dir.glob(f"{title}_{download_id}.*"):
                output_path = f
                break
        
        if not output_path.exists():
            raise HTTPException(status_code=500, detail="Download failed - file not found")
        
        filename = f"{title}.{output_path.suffix.lstrip('.')}"
        
        # Return file and clean up after
        return FileResponse(
            path=str(output_path),
            filename=filename,
            media_type='application/octet-stream',
            background=BackgroundTasks().add_task(lambda: output_path.unlink(missing_ok=True))
        )
        
    except yt_dlp.utils.DownloadError as e:
        raise HTTPException(status_code=400, detail=f"Download failed: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")


# ============== Convert Endpoint ==============

@router.post("/convert")
async def convert_video(request: ConvertRequest):
    """
    POST /convert - Download and convert to specified format
    
    Downloads video and converts to target format (mp3, mp4, webm, etc.)
    Supports custom quality and compression settings.
    """
    try:
        temp_dir = get_temp_dir()
        download_id = str(uuid.uuid4())[:8]
        
        # Get video info
        ydl_opts_info = {'quiet': True, 'no_warnings': True}
        with yt_dlp.YoutubeDL(ydl_opts_info) as ydl:
            info = ydl.extract_info(request.url, download=False)
        
        title = sanitize_filename(info.get('title', 'video'))
        
        # Map audio quality to bitrate
        audio_bitrate_map = {
            AudioQuality.LOW: '64',
            AudioQuality.MEDIUM: '128',
            AudioQuality.HIGH: '192',
            AudioQuality.VERY_HIGH: '320'
        }
        audio_bitrate = audio_bitrate_map.get(request.audio_quality, '192')
        
        # Configure based on output format
        output_path = temp_dir / f"{title}_{download_id}.{request.output_format}"
        
        if request.output_format == 'mp3':
            # Audio extraction
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'format': 'bestaudio[ext=m4a]/bestaudio/best',
                'outtmpl': str(temp_dir / f"{title}_{download_id}.%(ext)s"),
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': audio_bitrate,
                }]
            }
        else:
            # Video download with format conversion
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'format': get_quality_format(request.video_quality or 'best'),
                'outtmpl': str(output_path),
                'merge_output_format': request.output_format,
            }
            
            # Add compression postprocessor if needed
            if request.compress:
                ydl_opts['postprocessors'] = [{
                    'key': 'FFmpegVideoConvertor',
                    'preferedformat': request.output_format,
                }]
        
        # Download
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([request.url])
        
        # Find output file
        if not output_path.exists():
            for f in temp_dir.glob(f"{title}_{download_id}.*"):
                output_path = f
                break
        
        if not output_path.exists():
            raise HTTPException(status_code=500, detail="Conversion failed - file not found")
        
        filename = f"{title}.{request.output_format}"
        
        return FileResponse(
            path=str(output_path),
            filename=filename,
            media_type='application/octet-stream'
        )
        
    except yt_dlp.utils.DownloadError as e:
        raise HTTPException(status_code=400, detail=f"Download failed: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Conversion failed: {str(e)}")


# ============== Mobile Compression Endpoint ==============

@router.post("/mobile-compression")
async def mobile_compression(request: MobileCompressionRequest):
    """
    POST /mobile-compression - Download with mobile-optimized settings
    
    Preset compression for mobile devices:
    - Video: 480p MP4, optimized codec
    - Audio: 64kbps MP3 for minimal size
    
    Perfect for saving bandwidth and storage on mobile devices.
    """
    try:
        temp_dir = get_temp_dir()
        download_id = str(uuid.uuid4())[:8]
        
        # Get video info
        ydl_opts_info = {'quiet': True, 'no_warnings': True}
        with yt_dlp.YoutubeDL(ydl_opts_info) as ydl:
            info = ydl.extract_info(request.url, download=False)
        
        title = sanitize_filename(info.get('title', 'video'))
        
        # Determine resolution
        resolution = request.max_resolution or '480p'
        max_height = int(resolution.replace('p', ''))
        
        if request.audio_only:
            # Mobile-optimized audio: 64kbps MP3
            output_path = temp_dir / f"{title}_{download_id}_mobile.mp3"
            
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'format': 'bestaudio[ext=m4a]/bestaudio/best',
                'outtmpl': str(temp_dir / f"{title}_{download_id}_mobile.%(ext)s"),
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '64',  # Low bitrate for mobile
                }]
            }
        else:
            # Mobile-optimized video: 480p MP4
            output_path = temp_dir / f"{title}_{download_id}_mobile.mp4"
            
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'format': f'bestvideo[height<={max_height}]+bestaudio/best[height<={max_height}]',
                'outtmpl': str(output_path),
                'merge_output_format': 'mp4',
                'postprocessors': [{
                    'key': 'FFmpegVideoConvertor',
                    'preferedformat': 'mp4',
                }]
            }
        
        # Download
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([request.url])
        
        # Find output file
        if not output_path.exists():
            for f in temp_dir.glob(f"{title}_{download_id}_mobile.*"):
                output_path = f
                break
        
        if not output_path.exists():
            raise HTTPException(status_code=500, detail="Mobile compression failed - file not found")
        
        # Get file size
        file_size = output_path.stat().st_size
        file_size_mb = file_size / (1024 * 1024)
        
        filename = f"{title}_mobile.{output_path.suffix.lstrip('.')}"
        
        return FileResponse(
            path=str(output_path),
            filename=filename,
            media_type='application/octet-stream',
            headers={
                "X-File-Size-MB": f"{file_size_mb:.2f}",
                "X-Compression-Type": "mobile-optimized"
            }
        )
        
    except yt_dlp.utils.DownloadError as e:
        raise HTTPException(status_code=400, detail=f"Download failed: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Mobile compression failed: {str(e)}")
