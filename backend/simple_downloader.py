import yt_dlp
import os
import uuid

def download_video(url, format_id):
    outdir = "downloads"
    os.makedirs(outdir, exist_ok=True)

    filename = f"{uuid.uuid4()}.%(ext)s"
    filepath = os.path.join(outdir, filename)

    ydl_opts = {
        "format": format_id,
        "outtmpl": filepath,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    real_file = os.path.splitext(filepath.replace("%(ext)s", ""))[0]

    for f in os.listdir(outdir):
        if f.startswith(real_file.split(os.path.sep)[-1]):
            return os.path.join(outdir, f)

    return None
