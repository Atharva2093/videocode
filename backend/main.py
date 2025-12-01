from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from simple_downloader import download_video
import yt_dlp
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
def health():
    return {"status": "ok"}

@app.get("/api/metadata")
def metadata(url: str):
    try:
        ydl_opts = {"quiet": True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return {
                "title": info.get("title"),
                "thumbnail": info.get("thumbnail"),
                "formats": [
                    {"id": f["format_id"], "ext": f["ext"], "quality": f.get("height")}
                    for f in info.get("formats", [])
                    if f.get("vcodec") != "none"
                ],
            }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/download")
def download(url: str, format_id: str = "best"):
    filepath = download_video(url, format_id)
    return {"file": filepath}
