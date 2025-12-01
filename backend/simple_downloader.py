import yt_dlp
import os
import uuid


# Optimized yt-dlp options - use default client (ANDROID works best without JS runtime)
def get_ydl_opts():
    return {
        "quiet": True,
        "no_warnings": True,
        "format": "best[ext=mp4]/bestvideo[ext=mp4]+bestaudio[ext=m4a]/best",
        "merge_output_format": "mp4",
        "nocheckcertificate": True,
        "ignoreerrors": False,
        "no_color": True,
        "retries": 3,
        "fragment_retries": 3,
        # Use default extractor (ANDROID client) - works without JS runtime
        "extractor_args": {
            "youtube": {
                "player_client": ["android", "web"],
            }
        },
    }


def download_video(url, format_id="best"):
    outdir = "downloads"
    os.makedirs(outdir, exist_ok=True)

    filename = f"{uuid.uuid4()}.%(ext)s"
    filepath = os.path.join(outdir, filename)

    ydl_opts = get_ydl_opts()
    ydl_opts["outtmpl"] = filepath
    
    # Use format_id if provided, otherwise use best available
    if format_id and format_id != "best":
        ydl_opts["format"] = f"{format_id}+bestaudio/best"
    else:
        ydl_opts["format"] = "best[ext=mp4]/best"

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        
        # Check for DRM or live stream issues
        if info.get("is_live"):
            raise Exception("Live streams cannot be downloaded")
        
        # Find the downloaded file
        real_file = os.path.splitext(filepath.replace("%(ext)s", ""))[0]
        for f in os.listdir(outdir):
            if f.startswith(real_file.split(os.path.sep)[-1]):
                return os.path.join(outdir, f)
    
    raise Exception("Download failed - file not found")
