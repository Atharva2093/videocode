"""
Download endpoints - Phase 2
Includes: /download (queue-based), /download/direct, /convert, /mobile-compression
With streaming file response and mobile browser compatibility
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Response
from fastapi.responses import FileResponse, StreamingResponse
import os
import tempfile
import uuid
import asyncio
import yt_dlp
import subprocess
import shutil
import mimetypes
from pathlib import Path
from typing import Generator

from ..models import (
    DownloadRequest, DownloadResponse, DownloadProgress,
    QueueStatus, CancelRequest, DownloadStatus,
    DirectDownloadRequest, ConvertRequest, MobileCompressionRequest, AudioQuality
)
from ..worker import download_manager
from ..worker.ytdlp_downloader import downloader, DownloadError
from ..config import settings

router = APIRouter()


# ============== MIME Types for Mobile Compatibility ==============

MIME_TYPES = {
    'mp4': 'video/mp4',
    'webm': 'video/webm',
    'mkv': 'video/x-matroska',
    'avi': 'video/x-msvideo',
    'mov': 'video/quicktime',
    'mp3': 'audio/mpeg',
    'm4a': 'audio/mp4',
    'wav': 'audio/wav',
    'ogg': 'audio/ogg',
    'flac': 'audio/flac',
}


def get_mime_type(filename: str) -> str:
    """Get MIME type for file, with fallback for mobile compatibility"""
    ext = Path(filename).suffix.lower().lstrip('.')
    return MIME_TYPES.get(ext, 'application/octet-stream')


# ============== Helper Functions ==============

def get_temp_dir():
    """Get or create temp directory for downloads"""
    temp_dir = Path(settings.TEMP_DIR)
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


def iter_file_chunks(file_path: str, chunk_size: int = None) -> Generator[bytes, None, None]:
    """Generator to yield file chunks for streaming"""
    chunk_size = chunk_size or settings.CHUNK_SIZE
    with open(file_path, 'rb') as f:
        while chunk := f.read(chunk_size):
            yield chunk


async def cleanup_file_later(file_path: str, delay: int = 300):
    """Delete file after delay (5 minutes default)"""
    await asyncio.sleep(delay)
    try:
        if os.path.exists(file_path):
            os.unlink(file_path)
    except:
        pass


# ============== Queue-Based Download Endpoints ==============

@router.post("/download", response_model=DownloadResponse)
async def start_download(request: DownloadRequest):
    """
    POST /download - Queue-based download (async)
    
    Adds download to queue and returns task_id for tracking.
    Use GET /download/{task_id} to check status.
    """
    # Check if playlists are allowed
    if not settings.ALLOW_PLAYLISTS and ('list=' in request.url or '/playlist?' in request.url):
        raise HTTPException(status_code=400, detail="Playlist downloads are disabled")
    
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
async def download_file(task_id: str, background_tasks: BackgroundTasks):
    """
    GET /download/{task_id}/file - Download completed file with streaming
    
    Uses chunked streaming for mobile browser compatibility.
    Sets proper MIME types and Content-Disposition headers.
    """
    task = download_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task.status != DownloadStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Download not completed yet")
    
    if not task.file_path or not os.path.exists(task.file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    file_path = task.file_path
    filename = os.path.basename(file_path)
    file_size = os.path.getsize(file_path)
    mime_type = get_mime_type(filename)
    
    # Use streaming for large files (> 50MB) for better mobile compatibility
    if file_size > 50 * 1024 * 1024:
        return StreamingResponse(
            iter_file_chunks(file_path),
            media_type=mime_type,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Length": str(file_size),
                "Accept-Ranges": "bytes",
                "Cache-Control": "no-cache",
            }
        )
    
    # Use FileResponse for smaller files
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type=mime_type,
        headers={
            "Accept-Ranges": "bytes",
            "Cache-Control": "no-cache",
        }
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
async def direct_download(request: DirectDownloadRequest, background_tasks: BackgroundTasks):
    """
    POST /download/direct - Synchronous download returning file directly
    
    Downloads video/audio and returns the file as a streaming response.
    Uses chunked transfer for mobile browser compatibility.
    
    Features:
    - Retry logic with configurable attempts
    - Proper MIME types for mobile browsers
    - Auto cleanup of temp files
    - File size validation
    """
    try:
        # Use the reusable downloader with retry logic
        file_path = downloader.download(
            url=request.url,
            format=request.format,
            quality=request.quality,
            audio_only=request.audio_only,
            use_temp=True  # Download to temp, then stream
        )
        
        filename = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        mime_type = get_mime_type(filename)
        
        # Schedule cleanup after 5 minutes
        background_tasks.add_task(cleanup_file_later, file_path, 300)
        
        # Use streaming for better mobile compatibility
        return StreamingResponse(
            iter_file_chunks(file_path),
            media_type=mime_type,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Length": str(file_size),
                "Accept-Ranges": "bytes",
                "Cache-Control": "no-cache",
                "X-File-Size-MB": f"{file_size / (1024*1024):.2f}",
            }
        )
        
    except DownloadError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")


# ============== Convert Endpoint ==============

@router.post("/convert")
async def convert_video(request: ConvertRequest, background_tasks: BackgroundTasks):
    """
    POST /convert - Download and convert to specified format
    
    Downloads video and converts to target format (mp3, mp4, webm, etc.)
    Supports custom quality and compression settings.
    Uses streaming for mobile compatibility.
    """
    try:
        temp_dir = get_temp_dir()
        download_id = str(uuid.uuid4())[:8]
        
        # Get video info with retry
        metadata = downloader.extract_metadata(request.url)
        title = sanitize_filename(metadata.title)
        
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
                'retries': settings.MAX_RETRIES,
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
                'retries': settings.MAX_RETRIES,
            }
            
            # Add compression postprocessor if needed
            if request.compress:
                ydl_opts['postprocessors'] = [{
                    'key': 'FFmpegVideoConvertor',
                    'preferedformat': request.output_format,
                }]
        
        # Download with retry
        for attempt in range(settings.MAX_RETRIES):
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([request.url])
                break
            except Exception as e:
                if attempt == settings.MAX_RETRIES - 1:
                    raise
                await asyncio.sleep(settings.RETRY_DELAY_SECONDS)
        
        # Find output file
        if not output_path.exists():
            for f in temp_dir.glob(f"{title}_{download_id}.*"):
                output_path = f
                break
        
        if not output_path.exists():
            raise HTTPException(status_code=500, detail="Conversion failed - file not found")
        
        filename = f"{title}.{request.output_format}"
        file_size = output_path.stat().st_size
        mime_type = get_mime_type(filename)
        
        # Schedule cleanup
        background_tasks.add_task(cleanup_file_later, str(output_path), 300)
        
        # Use streaming for mobile compatibility
        return StreamingResponse(
            iter_file_chunks(str(output_path)),
            media_type=mime_type,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Length": str(file_size),
                "Accept-Ranges": "bytes",
                "X-File-Size-MB": f"{file_size / (1024*1024):.2f}",
            }
        )
        
    except yt_dlp.utils.DownloadError as e:
        raise HTTPException(status_code=400, detail=f"Download failed: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Conversion failed: {str(e)}")


# ============== Mobile Compression Endpoint ==============

@router.post("/mobile-compression")
async def mobile_compression(request: MobileCompressionRequest, background_tasks: BackgroundTasks):
    """
    POST /mobile-compression - Download with mobile-optimized settings
    
    Preset compression for mobile devices:
    - Video: 480p MP4, optimized codec
    - Audio: 64kbps MP3 for minimal size
    
    Perfect for saving bandwidth and storage on mobile devices.
    Uses streaming for mobile browser compatibility.
    """
    try:
        temp_dir = get_temp_dir()
        download_id = str(uuid.uuid4())[:8]
        
        # Get video info with retry
        metadata = downloader.extract_metadata(request.url)
        title = sanitize_filename(metadata.title)
        
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
                'retries': settings.MAX_RETRIES,
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
                'retries': settings.MAX_RETRIES,
                'postprocessors': [{
                    'key': 'FFmpegVideoConvertor',
                    'preferedformat': 'mp4',
                }]
            }
        
        # Download with retry
        for attempt in range(settings.MAX_RETRIES):
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([request.url])
                break
            except Exception as e:
                if attempt == settings.MAX_RETRIES - 1:
                    raise
                await asyncio.sleep(settings.RETRY_DELAY_SECONDS)
        
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
        mime_type = get_mime_type(filename)
        
        # Schedule cleanup
        background_tasks.add_task(cleanup_file_later, str(output_path), 300)
        
        # Use streaming for mobile compatibility
        return StreamingResponse(
            iter_file_chunks(str(output_path)),
            media_type=mime_type,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Length": str(file_size),
                "Accept-Ranges": "bytes",
                "X-File-Size-MB": f"{file_size_mb:.2f}",
                "X-Compression-Type": "mobile-optimized"
            }
        )
        
    except yt_dlp.utils.DownloadError as e:
        raise HTTPException(status_code=400, detail=f"Download failed: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Mobile compression failed: {str(e)}")
