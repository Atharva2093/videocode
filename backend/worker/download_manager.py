"""
Download Manager - Handles download queue and worker threads
"""

import asyncio
import uuid
import os
from datetime import datetime
from typing import Dict, Optional, List
from concurrent.futures import ThreadPoolExecutor
import threading

import yt_dlp

from models import DownloadProgress, DownloadStatus, QueueStatus
from config import settings


class DownloadManager:
    """Manages download queue and worker threads"""
    
    def __init__(self):
        self.tasks: Dict[str, DownloadProgress] = {}
        self.queue: asyncio.Queue = None
        self.executor: ThreadPoolExecutor = None
        self.workers: List[asyncio.Task] = []
        self.cancel_flags: Dict[str, bool] = {}
        self.lock = threading.Lock()
        self._running = False
    
    async def start(self):
        """Start the download manager"""
        self.queue = asyncio.Queue(maxsize=settings.MAX_QUEUE_SIZE)
        self.executor = ThreadPoolExecutor(max_workers=settings.MAX_CONCURRENT_DOWNLOADS)
        self._running = True
        
        # Start worker tasks
        for i in range(settings.MAX_CONCURRENT_DOWNLOADS):
            worker = asyncio.create_task(self._worker(f"worker-{i}"))
            self.workers.append(worker)
        
        print(f"✅ Download manager started with {settings.MAX_CONCURRENT_DOWNLOADS} workers")
    
    async def stop(self):
        """Stop the download manager"""
        self._running = False
        
        # Cancel all pending downloads
        for task_id in list(self.cancel_flags.keys()):
            self.cancel_flags[task_id] = True
        
        # Cancel worker tasks
        for worker in self.workers:
            worker.cancel()
        
        # Shutdown executor
        if self.executor:
            self.executor.shutdown(wait=False)
        
        print("✅ Download manager stopped")
    
    async def add_download(
        self,
        url: str,
        format: str = "mp4",
        quality: str = "best",
        audio_only: bool = False,
        playlist_items: Optional[List[int]] = None
    ) -> str:
        """Add a download to the queue"""
        
        if self.queue.full():
            raise ValueError("Download queue is full. Please wait for some downloads to complete.")
        
        task_id = str(uuid.uuid4())[:8]
        now = datetime.now()
        
        task = DownloadProgress(
            task_id=task_id,
            status=DownloadStatus.QUEUED,
            progress=0.0,
            created_at=now,
            updated_at=now
        )
        
        with self.lock:
            self.tasks[task_id] = task
            self.cancel_flags[task_id] = False
        
        # Add to queue
        await self.queue.put({
            'task_id': task_id,
            'url': url,
            'format': format,
            'quality': quality,
            'audio_only': audio_only,
            'playlist_items': playlist_items
        })
        
        return task_id
    
    async def _worker(self, worker_name: str):
        """Worker coroutine that processes downloads"""
        print(f"🔧 {worker_name} started")
        
        while self._running:
            try:
                # Get next download from queue
                download_info = await asyncio.wait_for(
                    self.queue.get(),
                    timeout=1.0
                )
                
                task_id = download_info['task_id']
                
                # Check if cancelled before starting
                if self.cancel_flags.get(task_id, False):
                    self._update_task(task_id, status=DownloadStatus.CANCELLED)
                    continue
                
                # Process download in thread pool
                await asyncio.get_event_loop().run_in_executor(
                    self.executor,
                    self._download_video,
                    download_info
                )
                
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"❌ {worker_name} error: {e}")
    
    def _download_video(self, download_info: dict):
        """Download video (runs in thread pool)"""
        task_id = download_info['task_id']
        url = download_info['url']
        format = download_info['format']
        quality = download_info['quality']
        audio_only = download_info['audio_only']
        playlist_items = download_info.get('playlist_items')
        
        self._update_task(task_id, status=DownloadStatus.FETCHING_INFO)
        
        try:
            # Configure format
            if audio_only:
                format_spec = "bestaudio/best"
                postprocessors = [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }]
                ext = "mp3"
            else:
                format_spec = f"{quality}[ext={format}]/{quality}/best"
                postprocessors = []
                ext = format
            
            # Configure yt-dlp options
            ydl_opts = {
                'format': format_spec,
                'outtmpl': os.path.join(settings.DOWNLOAD_DIR, '%(title)s.%(ext)s'),
                'progress_hooks': [lambda d: self._progress_hook(d, task_id)],
                'postprocessors': postprocessors,
                'quiet': True,
                'no_warnings': True,
                'ignoreerrors': True,
            }
            
            # Add playlist items filter if specified
            if playlist_items:
                ydl_opts['playlist_items'] = ','.join(map(str, playlist_items))
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Extract info first
                info = ydl.extract_info(url, download=False)
                title = info.get('title', 'Video')
                
                self._update_task(
                    task_id,
                    title=title,
                    status=DownloadStatus.DOWNLOADING
                )
                
                # Check if cancelled
                if self.cancel_flags.get(task_id, False):
                    self._update_task(task_id, status=DownloadStatus.CANCELLED)
                    return
                
                # Download
                ydl.download([url])
                
                # Get output file path
                if info.get('_type') == 'playlist':
                    # For playlists, file path handling is different
                    file_path = settings.DOWNLOAD_DIR
                else:
                    filename = ydl.prepare_filename(info)
                    if audio_only:
                        filename = os.path.splitext(filename)[0] + ".mp3"
                    file_path = filename
                
                self._update_task(
                    task_id,
                    status=DownloadStatus.COMPLETED,
                    progress=100.0,
                    file_path=file_path
                )
                
        except Exception as e:
            self._update_task(
                task_id,
                status=DownloadStatus.FAILED,
                error=str(e)
            )
    
    def _progress_hook(self, d: dict, task_id: str):
        """Progress hook for yt-dlp"""
        # Check for cancellation
        if self.cancel_flags.get(task_id, False):
            raise Exception("Download cancelled")
        
        if d['status'] == 'downloading':
            try:
                percent_str = d.get('_percent_str', '0%').replace('%', '').strip()
                progress = float(percent_str)
                speed = d.get('_speed_str', 'N/A')
                eta = d.get('_eta_str', 'N/A')
                downloaded = d.get('downloaded_bytes', 0)
                total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                
                self._update_task(
                    task_id,
                    progress=progress,
                    speed=speed,
                    eta=eta,
                    downloaded_bytes=downloaded,
                    total_bytes=total
                )
            except:
                pass
        
        elif d['status'] == 'finished':
            self._update_task(
                task_id,
                status=DownloadStatus.PROCESSING,
                progress=100.0
            )
    
    def _update_task(self, task_id: str, **kwargs):
        """Update task status"""
        with self.lock:
            if task_id in self.tasks:
                task = self.tasks[task_id]
                for key, value in kwargs.items():
                    if hasattr(task, key):
                        setattr(task, key, value)
                task.updated_at = datetime.now()
    
    def get_task(self, task_id: str) -> Optional[DownloadProgress]:
        """Get task by ID"""
        return self.tasks.get(task_id)
    
    async def cancel_download(self, task_id: str) -> bool:
        """Cancel a download"""
        with self.lock:
            if task_id in self.tasks:
                task = self.tasks[task_id]
                if task.status in [DownloadStatus.QUEUED, DownloadStatus.DOWNLOADING, DownloadStatus.FETCHING_INFO]:
                    self.cancel_flags[task_id] = True
                    task.status = DownloadStatus.CANCELLED
                    task.updated_at = datetime.now()
                    return True
        return False
    
    def remove_task(self, task_id: str) -> bool:
        """Remove a task from history"""
        with self.lock:
            if task_id in self.tasks:
                del self.tasks[task_id]
                self.cancel_flags.pop(task_id, None)
                return True
        return False
    
    def clear_completed(self) -> int:
        """Clear completed and failed tasks"""
        count = 0
        with self.lock:
            to_remove = [
                tid for tid, task in self.tasks.items()
                if task.status in [DownloadStatus.COMPLETED, DownloadStatus.FAILED, DownloadStatus.CANCELLED]
            ]
            for tid in to_remove:
                del self.tasks[tid]
                self.cancel_flags.pop(tid, None)
                count += 1
        return count
    
    def get_queue_status(self) -> QueueStatus:
        """Get current queue status"""
        with self.lock:
            active = sum(1 for t in self.tasks.values() if t.status in [DownloadStatus.DOWNLOADING, DownloadStatus.FETCHING_INFO, DownloadStatus.PROCESSING])
            queued = sum(1 for t in self.tasks.values() if t.status == DownloadStatus.QUEUED)
            completed = sum(1 for t in self.tasks.values() if t.status == DownloadStatus.COMPLETED)
            failed = sum(1 for t in self.tasks.values() if t.status in [DownloadStatus.FAILED, DownloadStatus.CANCELLED])
            
            return QueueStatus(
                active_downloads=active,
                queued_downloads=queued,
                completed_downloads=completed,
                failed_downloads=failed,
                tasks=list(self.tasks.values())
            )
