import yt_dlp
import os
import uuid

# Path to cookies file
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
COOKIES_FILE = os.path.join(BACKEND_DIR, "cookies.txt")

# Check for Render secrets path
RENDER_COOKIES = "/etc/secrets/cookies.txt"
if os.path.exists(RENDER_COOKIES):
    COOKIES_FILE = RENDER_COOKIES


def get_ydl_opts():
    """
    Optimized yt-dlp options with cookie support to bypass bot detection.
    """
    opts = {
        "quiet": True,
        "no_warnings": True,
        "format": "best[ext=mp4]/bestvideo[ext=mp4]+bestaudio[ext=m4a]/best",
        "merge_output_format": "mp4",
        "nocheckcertificate": True,
        "ignoreerrors": False,
        "no_color": True,
        "retries": 3,
        "fragment_retries": 3,
        # Use iOS client - most reliable for bypassing restrictions
        "extractor_args": {
            "youtube": {
                "player_client": ["ios", "android", "web"],
            }
        },
    }
    
    # Add cookies if file exists
    if os.path.exists(COOKIES_FILE):
        opts["cookiefile"] = COOKIES_FILE
    
    return opts


def download_video(url, format_id="best"):
    outdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "downloads")
    os.makedirs(outdir, exist_ok=True)

    file_id = str(uuid.uuid4())
    filepath_template = os.path.join(outdir, f"{file_id}.%(ext)s")

    ydl_opts = get_ydl_opts()
    ydl_opts["outtmpl"] = filepath_template
    
    # Handle format selection
    if format_id == "mp3":
        ydl_opts["format"] = "bestaudio/best"
        ydl_opts["postprocessors"] = [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }]
    elif format_id and format_id != "best":
        # Specific format_id - merge with best audio if video-only
        ydl_opts["format"] = f"{format_id}+bestaudio[ext=m4a]/{format_id}+bestaudio/{format_id}/best"
        ydl_opts["merge_output_format"] = "mp4"
    else:
        ydl_opts["format"] = "best[ext=mp4]/bestvideo[ext=mp4]+bestaudio[ext=m4a]/best"

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        
        # Check for live stream issues
        if info.get("is_live"):
            raise Exception("Live streams cannot be downloaded")
    
    # Find the downloaded file by matching the UUID
    for f in os.listdir(outdir):
        if f.startswith(file_id):
            full_path = os.path.join(outdir, f)
            if os.path.exists(full_path):
                return full_path
    
    raise Exception("Download failed - file not found")
