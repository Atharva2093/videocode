"""
YouTube Video Downloader - FastAPI Backend
Main application entry point
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import os
import time

from .routes import download, video_info, health
from .config import settings
from .worker import download_manager
from .worker.ytdlp_downloader import downloader


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    # Startup
    print("🚀 Starting YouTube Downloader API...")
    print(f"📁 Download directory: {settings.DOWNLOAD_DIR}")
    print(f"📁 Temp directory: {settings.TEMP_DIR}")
    print(f"🔧 Max concurrent downloads: {settings.MAX_CONCURRENT_DOWNLOADS}")
    print(f"📦 Max file size: {settings.MAX_FILE_SIZE_MB}MB")
    print(f"🎬 Allow playlists: {settings.ALLOW_PLAYLISTS}")
    
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
        print(f"🧹 Cleaned up {deleted} old temp files on startup")
    
    yield
    
    # Shutdown
    print("🛑 Shutting down YouTube Downloader API...")
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


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Simple rate limiting middleware"""
    client_ip = request.client.host
    current_time = time.time()
    
    # Clean old entries
    request_counts[client_ip] = [
        t for t in request_counts.get(client_ip, [])
        if current_time - t < settings.RATE_LIMIT_WINDOW
    ]
    
    # Check rate limit
    if len(request_counts.get(client_ip, [])) >= settings.RATE_LIMIT_REQUESTS:
        return JSONResponse(
            status_code=429,
            content={"detail": "Too many requests. Please slow down."}
        )
    
    # Add current request
    request_counts.setdefault(client_ip, []).append(current_time)
    
    response = await call_next(request)
    return response


# Include routers
app.include_router(health.router, prefix="/api", tags=["Health"])
app.include_router(video_info.router, prefix="/api", tags=["Video Info"])
app.include_router(download.router, prefix="/api", tags=["Download"])

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
