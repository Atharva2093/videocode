"""
YouTube Video Downloader - FastAPI Backend
Main application entry point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os

from .routes import download, video_info, health
from .config import settings
from .worker import download_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    # Startup
    print("🚀 Starting YouTube Downloader API...")
    
    # Create download directory if it doesn't exist
    os.makedirs(settings.DOWNLOAD_DIR, exist_ok=True)
    os.makedirs(settings.TEMP_DIR, exist_ok=True)
    
    # Start the download worker
    await download_manager.start()
    
    yield
    
    # Shutdown
    print("🛑 Shutting down YouTube Downloader API...")
    await download_manager.stop()


# Create FastAPI application
app = FastAPI(
    title="YouTube Video Downloader API",
    description="A powerful API for downloading YouTube videos and playlists",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
        "version": "1.0.0",
        "docs": "/api/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
