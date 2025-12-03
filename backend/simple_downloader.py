import logging
import os
import re
import shutil
import tempfile
import time
from dataclasses import dataclass
from typing import Optional

import yt_dlp

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
COOKIES_FILE = os.path.join(BACKEND_DIR, "cookies.txt")

if os.path.exists("/etc/secrets/cookies.txt"):
    COOKIES_FILE = "/etc/secrets/cookies.txt"


@dataclass
class DownloadArtifact:
    filepath: str
    filename: str
    filesize: Optional[int]
    workspace: str


def is_ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None


def get_ffmpeg_location() -> str:
    return shutil.which("ffmpeg") or "not found"


def get_yt_dlp_version() -> str:
    return yt_dlp.version.__version__


def sanitize_title(title: Optional[str]) -> str:
    if not title:
        return "video"
    safe = re.sub(r'[\\/:*?"<>|]', "", title)
    safe = re.sub(r"\s+", " ", safe).strip()
    return safe[:150] if safe else "video"


def _build_format_selector(format_id: str) -> str:
    if format_id and format_id != "best":
        return f"{format_id}+bestaudio/{format_id}/bestvideo+bestaudio/best"
    return "bestvideo+bestaudio/best"


def prepare_download(url: str, format_id: str = "best") -> DownloadArtifact:
    workspace = tempfile.mkdtemp(prefix="yt-stream-")
    output_template = os.path.join(workspace, "video.%(ext)s")

    ydl_opts = {
        "outtmpl": output_template,
        "quiet": True,
        "no_warnings": True,
        "nocheckcertificate": True,
        "retries": 5,
        "fragment_retries": 5,
        "socket_timeout": 30,
        "noprogress": True,
        "format": _build_format_selector(format_id),
        "merge_output_format": "mp4",
    }

    if os.path.exists(COOKIES_FILE):
        ydl_opts["cookiefile"] = COOKIES_FILE
        logger.info("Using cookies file for download")

    if is_ffmpeg_available():
        ydl_opts["ffmpeg_location"] = get_ffmpeg_location()
    else:
        logger.warning("FFmpeg not available - falling back to progressive formats only")
        preferred = format_id if format_id and format_id != "best" else "best"
        ydl_opts["format"] = f"{preferred}[ext=mp4]/best[ext=mp4]/best"
        ydl_opts.pop("merge_output_format", None)

    logger.info("Preparing download workspace at %s", workspace)

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if not info:
                raise RuntimeError("Failed to extract video info")
            if info.get("is_live"):
                raise RuntimeError("Live streams cannot be downloaded")

            requested = info.get("requested_downloads") or []
            candidate_path = None
            if requested:
                candidate_path = requested[0].get("filepath")
            if not candidate_path:
                candidate_path = info.get("_filename")
            if not candidate_path or not os.path.exists(candidate_path):
                for entry in os.listdir(workspace):
                    test_path = os.path.join(workspace, entry)
                    if os.path.isfile(test_path):
                        candidate_path = test_path
                        break

            if not candidate_path or not os.path.exists(candidate_path):
                raise RuntimeError("Download produced no file")

            ext = os.path.splitext(candidate_path)[1] or ".mp4"
            safe_title = sanitize_title(info.get("title"))
            final_name = f"{safe_title}{ext}"
            final_path = os.path.join(workspace, final_name)

            if candidate_path != final_path:
                shutil.move(candidate_path, final_path)

            filesize = os.path.getsize(final_path) if os.path.exists(final_path) else None
            logger.info("Prepared artifact %s (%s bytes)", final_name, filesize or "unknown")

            return DownloadArtifact(
                filepath=final_path,
                filename=final_name,
                filesize=filesize,
                workspace=workspace,
            )
    except Exception:
        shutil.rmtree(workspace, ignore_errors=True)
        raise


def cleanup_artifact(artifact: DownloadArtifact) -> None:
    try:
        shutil.rmtree(artifact.workspace, ignore_errors=True)
        logger.info("Cleaned up workspace %s", artifact.workspace)
    except Exception as exc:
        logger.warning("Failed to clean workspace %s: %s", artifact.workspace, exc)


def cleanup_stale_workspaces(max_age_hours: int = 6) -> None:
    now = time.time()
    max_age = max_age_hours * 3600
    tmp_dir = tempfile.gettempdir()
    removed = 0
    for entry in os.listdir(tmp_dir):
        if not entry.startswith("yt-stream-"):
            continue
        path = os.path.join(tmp_dir, entry)
        try:
            if os.path.isdir(path) and now - os.path.getmtime(path) > max_age:
                shutil.rmtree(path, ignore_errors=True)
                removed += 1
        except Exception:
            continue
    if removed:
        logger.info("Removed %s stale workspaces", removed)
