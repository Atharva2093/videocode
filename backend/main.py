from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from simple_downloader import download_video, get_ydl_opts
import yt_dlp
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)


def is_drm_error(error_str: str) -> bool:
    """Check if the error is related to DRM or extraction issues"""
    drm_keywords = ["DRM", "drm", "protected", "nsig", "signature", "SABR", "unplayable"]
    return any(keyword in error_str for keyword in drm_keywords)


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/metadata")
def metadata(url: str):
    ydl_opts = get_ydl_opts()
    ydl_opts["skip_download"] = True
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # Check for live streams
            if info.get("is_live"):
                return JSONResponse(
                    status_code=400,
                    content={"error": "Live streams cannot be downloaded"}
                )
            
            # Filter formats that have valid URLs and are not DRM protected
            valid_formats = []
            for f in info.get("formats", []):
                # Skip formats without URLs or with DRM
                if not f.get("url"):
                    continue
                if f.get("has_drm"):
                    continue
                if f.get("vcodec") == "none":
                    continue
                    
                valid_formats.append({
                    "id": f["format_id"],
                    "ext": f.get("ext", "mp4"),
                    "quality": f.get("height"),
                    "filesize": f.get("filesize"),
                })
            
            # If no formats found, still return basic info (download will use fallback)
            return {
                "title": info.get("title"),
                "thumbnail": info.get("thumbnail"),
                "duration": info.get("duration"),
                "formats": valid_formats if valid_formats else [{"id": "best", "ext": "mp4", "quality": "best"}],
            }
            
    except Exception as e:
        error_str = str(e)
        
        # Check for DRM/extraction errors
        if is_drm_error(error_str):
            return JSONResponse(
                status_code=400,
                content={"error": "This video cannot be downloaded due to DRM or YouTube restrictions."}
            )
        
        # Try fallback extraction with extract_flat
        try:
            ydl_opts["extract_flat"] = True
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                return {
                    "title": info.get("title", "Unknown"),
                    "thumbnail": info.get("thumbnail"),
                    "formats": [{"id": "best", "ext": "mp4", "quality": "best"}],
                }
        except:
            return JSONResponse(
                status_code=400,
                content={"error": f"Failed to extract video info: {error_str}"}
            )


@app.get("/api/download")
def download(url: str, format_id: str = "best"):
    try:
        filepath = download_video(url, format_id)
        if not filepath or not os.path.exists(filepath):
            return JSONResponse(
                status_code=500,
                content={"error": "Download failed - file not created"}
            )
        
        filename = os.path.basename(filepath)
        
        # Determine media type based on extension
        ext = os.path.splitext(filename)[1].lower()
        if ext == ".mp3":
            media_type = "audio/mpeg"
        elif ext == ".webm":
            media_type = "video/webm"
        else:
            media_type = "video/mp4"
        
        return FileResponse(
            filepath,
            media_type=media_type,
            filename=filename,
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
    except Exception as e:
        error_str = str(e)
        
        if is_drm_error(error_str):
            return JSONResponse(
                status_code=400,
                content={"error": "This video cannot be downloaded due to DRM or YouTube restrictions."}
            )
        
        return JSONResponse(
            status_code=500,
            content={"error": f"Download failed: {error_str}"}
        )
