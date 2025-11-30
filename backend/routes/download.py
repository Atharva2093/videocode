"""
Download endpoints
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import os

from ..models import (
    DownloadRequest, DownloadResponse, DownloadProgress,
    QueueStatus, CancelRequest, DownloadStatus
)
from ..worker import download_manager
from ..config import settings

router = APIRouter()


@router.post("/download", response_model=DownloadResponse)
async def start_download(request: DownloadRequest):
    """
    Start a new download task
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
    Get the status of a download task
    """
    task = download_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.post("/download/cancel")
async def cancel_download(request: CancelRequest):
    """
    Cancel a download task
    """
    success = await download_manager.cancel_download(request.task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found or already completed")
    return {"message": "Download cancelled", "task_id": request.task_id}


@router.delete("/download/{task_id}")
async def remove_download(task_id: str):
    """
    Remove a download task from history
    """
    success = download_manager.remove_task(task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"message": "Task removed", "task_id": task_id}


@router.get("/queue", response_model=QueueStatus)
async def get_queue_status():
    """
    Get the current download queue status
    """
    return download_manager.get_queue_status()


@router.get("/download/{task_id}/file")
async def download_file(task_id: str):
    """
    Download the completed file
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
    Clear completed and failed downloads from queue
    """
    count = download_manager.clear_completed()
    return {"message": f"Cleared {count} tasks"}
