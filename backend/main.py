"""
YouTube Video Downloader - FastAPI Backend
Main application entry point
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import os
import sys
import time

# Add backend directory to path for imports
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from routes import download, video_info, health, search
from config import settings
from worker import download_manager
from worker.ytdlp_downloader import downloader
from errors import (
    AppException,
    app_exception_handler,
    http_exception_handler,
    general_exception_handler,
    log_info,
    log_error
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    # Startup
    log_info("🚀 Starting YouTube Downloader API...")
    log_info(f"📁 Download directory: {settings.DOWNLOAD_DIR}")
    log_info(f"📁 Temp directory: {settings.TEMP_DIR}")
    log_info(f"🔧 Max concurrent downloads: {settings.MAX_CONCURRENT_DOWNLOADS}")
    log_info(f"📦 Max file size: {settings.MAX_FILE_SIZE_MB}MB")
    log_info(f"🎬 Allow playlists: {settings.ALLOW_PLAYLISTS}")
    
    # Create download directory if it doesn't exist
    os.makedirs(settings.DOWNLOAD_DIR, exist_ok=True)
    os.makedirs(settings.TEMP_DIR, exist_ok=True)
    
    # Start the download worker
    await download_manager.start()
    
    # Start temp file cleanup scheduler
    await downloader.start_cleanup_scheduler()
    
    # Clean up any old temp files on startup
    deleted = downloader.cleanup_temp_files()
    if deleted > 0:
        log_info(f"🧹 Cleaned up {deleted} old temp files on startup")
    
    yield
    
    # Shutdown
    log_info("🛑 Shutting down YouTube Downloader API...")
    await download_manager.stop()
    downloader.stop_cleanup_scheduler()


# Create FastAPI application
app = FastAPI(
    title="YouTube Video Downloader API",
    description="A powerful API for downloading YouTube videos and playlists",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# Register exception handlers
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Configure CORS - Restrict to specific domains
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
    expose_headers=[
        "Content-Disposition",
        "Content-Length",
        "Content-Type",
        "X-File-Size-MB",
        "X-Compression-Type"
    ],
)


# Add rate limiting middleware (simple implementation)
request_counts = {}
download_counts = {}


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Rate limiting middleware with separate limits for downloads"""
    client_ip = request.client.host
    current_time = time.time()
    
    # Clean old entries
    request_counts[client_ip] = [
        t for t in request_counts.get(client_ip, [])
        if current_time - t < settings.RATE_LIMIT_WINDOW
    ]
    
    download_counts[client_ip] = [
        t for t in download_counts.get(client_ip, [])
        if current_time - t < settings.RATE_LIMIT_WINDOW
    ]
    
    # Check general rate limit
    if len(request_counts.get(client_ip, [])) >= settings.RATE_LIMIT_REQUESTS:
        return JSONResponse(
            status_code=429,
            content={
                "detail": "Too many requests. Please slow down.",
                "error_code": "RATE_LIMIT_EXCEEDED",
                "retry_after": settings.RATE_LIMIT_WINDOW
            }
        )
    
    # Check download-specific rate limit
    is_download_request = (
        request.url.path.startswith('/api/download') and 
        request.method == 'POST'
    )
    
    if is_download_request:
        if len(download_counts.get(client_ip, [])) >= settings.RATE_LIMIT_DOWNLOADS:
            return JSONResponse(
                status_code=429,
                content={
                    "detail": f"Too many download requests. Maximum {settings.RATE_LIMIT_DOWNLOADS} downloads per minute.",
                    "error_code": "DOWNLOAD_RATE_LIMIT_EXCEEDED",
                    "retry_after": settings.RATE_LIMIT_WINDOW
                }
            )
        download_counts.setdefault(client_ip, []).append(current_time)
    
    # Add current request
    request_counts.setdefault(client_ip, []).append(current_time)
    
    response = await call_next(request)
    return response


# Include routers
app.include_router(health.router, prefix="/api", tags=["Health"])
app.include_router(video_info.router, prefix="/api", tags=["Video Info"])
app.include_router(download.router, prefix="/api", tags=["Download"])
app.include_router(search.router, prefix="/api", tags=["Search & Subtitles"])

# Serve downloaded files
if os.path.exists(settings.DOWNLOAD_DIR):
    app.mount("/downloads", StaticFiles(directory=settings.DOWNLOAD_DIR), name="downloads")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "YouTube Video Downloader API",
        "version": "2.0.0",
        "docs": "/api/docs",
        "features": {
            "max_file_size_mb": settings.MAX_FILE_SIZE_MB,
            "allow_playlists": settings.ALLOW_PLAYLISTS,
            "max_video_duration_minutes": settings.MAX_VIDEO_DURATION // 60,
            "max_concurrent_downloads": settings.MAX_CONCURRENT_DOWNLOADS
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
