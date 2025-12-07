import logging
import os
import shutil
import sys
import tempfile
import time
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional

# Workaround for termios not available on Windows
if sys.platform == "win32":
    import types
    sys.modules["termios"] = types.ModuleType("termios")
    sys.modules["tty"] = types.ModuleType("tty")
    sys.modules["pty"] = types.ModuleType("pty")

import yt_dlp

from exceptions import InvalidURLError

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
    safe = "".join(c for c in title if c not in '\\/:*?"<>|')
    safe = " ".join(safe.split())
    return safe[:150] if safe else "video"


def cleanup_stale_workspaces(max_age_hours: int = 6) -> None:
    tmp_dir = tempfile.gettempdir()
    now = time.time()
    max_age = max_age_hours * 3600
    removed = 0

    for name in os.listdir(tmp_dir):
        if not name.startswith("yt-stream-"):
            continue
        path = os.path.join(tmp_dir, name)
        try:
            if os.path.isdir(path) and now - os.path.getmtime(path) > max_age:
                shutil.rmtree(path, ignore_errors=True)
                removed += 1
        except Exception:
            continue

    if removed:
        logger.info("Removed %d stale workspaces", removed)


def prepare_cookie_jar(dest_dir: Optional[str] = None) -> Optional[str]:
    if not os.path.exists(COOKIES_FILE):
        return None

    try:
        if dest_dir:
            os.makedirs(dest_dir, exist_ok=True)
            target_path = os.path.join(dest_dir, "cookies.txt")
        else:
            fd, target_path = tempfile.mkstemp(prefix="yt-cookies-", suffix=".txt")
            os.close(fd)

        shutil.copyfile(COOKIES_FILE, target_path)
        try:
            os.chmod(target_path, 0o600)
        except (PermissionError, NotImplementedError):
            pass

        return target_path
    except Exception as exc:
        logger.warning("Failed to prepare cookie jar: %s", exc)
        return None


def cleanup_cookie_jar(temp_path: Optional[str]) -> None:
    if not temp_path or temp_path == COOKIES_FILE:
        return
    try:
        os.remove(temp_path)
    except FileNotFoundError:
        pass
    except Exception as exc:
        logger.warning("Failed to remove temp cookies file %s: %s", temp_path, exc)


def acquire_cookiefile(dest_dir: Optional[str] = None) -> tuple[Optional[str], Optional[str]]:
    """Return a tuple of (cookiefile_path, temp_path) for use in yt-dlp."""
    path = prepare_cookie_jar(dest_dir=dest_dir)
    return path, path


def release_cookiefile(temp_path: Optional[str]) -> None:
    cleanup_cookie_jar(temp_path)


def _build_format_selector(format_id: str) -> str:
    if format_id and format_id != "best":
        return f"{format_id}+bestaudio/{format_id}/bestvideo+bestaudio/best"
    return "bestvideo+bestaudio/best"


def _is_supported_mp4_format(entry: Dict) -> bool:
    if not entry or entry.get("has_drm"):
        return False
    if entry.get("ext") != "mp4":
        return False
    if entry.get("vcodec", "none") in ("none", None):
        return False
    if not entry.get("height"):
        return False

    protocol = (entry.get("protocol") or "").lower()
    if protocol in {"m3u8", "m3u8_native", "dash", "http_dash_segments"}:
        return False

    return True


def filter_supported_formats(formats: Iterable[Dict]) -> List[Dict]:
    filtered = [entry for entry in formats if _is_supported_mp4_format(entry)]
    filtered.sort(key=lambda x: (x.get("height") or 0, x.get("fps") or 0), reverse=True)
    return filtered


def get_ydl_opts(output_template: str, format_id: str, cookiefile: Optional[str]) -> dict:
    ydl_opts = {
        "outtmpl": output_template,
        "quiet": True,
        "no_warnings": True,
        "nocheckcertificate": True,
        "retries": 10,
        "fragment_retries": 10,
        "file_access_retries": 10,
        "concurrent_fragment_downloads": 5,
        "http_chunk_size": "10M",
        "socket_timeout": 30,
        "throttledrate": 0,
        "bidi_workaround": True,
        "noprogress": True,
        "no_color": True,
        "format": _build_format_selector(format_id),
        "merge_output_format": "mp4",
        "no_write_cookie_file": True,
        "cookiesfrombrowser": None,
        "no_cache_dir": True,
        "reject_cookies": True,
        "color": "no_color",
    }

    if cookiefile:
        ydl_opts["cookiefile"] = cookiefile

    if is_ffmpeg_available():
        ydl_opts["ffmpeg_location"] = get_ffmpeg_location()
    else:
        logger.warning("FFmpeg not available - falling back to progressive MP4 formats")
        preferred = format_id if format_id and format_id != "best" else "best"
        ydl_opts["format"] = f"{preferred}[ext=mp4]/best[ext=mp4]/best"
        ydl_opts.pop("merge_output_format", None)

    return ydl_opts


def build_metadata_opts(cookiefile: Optional[str]) -> dict:
    opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "nocheckcertificate": True,
        "socket_timeout": 15,
        "retries": 10,
        "fragment_retries": 10,
        "file_access_retries": 5,
        "noprogress": True,
        "no_color": True,
        "no_write_cookie_file": True,
        "cookiesfrombrowser": None,
        "no_cache_dir": True,
        "reject_cookies": True,
        "color": "no_color",
    }

    if cookiefile:
        opts["cookiefile"] = cookiefile

    return opts


def prepare_download(url: str, format_id: str = "best") -> DownloadArtifact:
    cleanup_stale_workspaces(max_age_hours=6)

    workspace = tempfile.mkdtemp(prefix="yt-stream-")
    output_template = os.path.join(workspace, "video.%(ext)s")

    cookiefile, temp_cookie = acquire_cookiefile(dest_dir=workspace)
    ydl_opts = get_ydl_opts(output_template, format_id, cookiefile)

    try:
        metadata_opts = build_metadata_opts(cookiefile)
        with yt_dlp.YoutubeDL(metadata_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        if not info:
            raise RuntimeError("Failed to extract video info")
        if info.get("is_live"):
            raise RuntimeError("Live streams cannot be downloaded")

        valid_formats = filter_supported_formats(info.get("formats", []))
        allowed_ids = {fmt.get("format_id") for fmt in valid_formats if fmt.get("format_id")}
        if format_id and format_id != "best" and format_id not in allowed_ids:
            raise InvalidURLError(message="Invalid or unsupported format ID.")

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)

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

        safe_title = sanitize_title(info.get("title"))
        final_name = f"{safe_title}.mp4"
        final_path = os.path.join(workspace, final_name)

        if os.path.normcase(candidate_path) != os.path.normcase(final_path):
            shutil.move(candidate_path, final_path)

        filesize = os.path.getsize(final_path) if os.path.exists(final_path) else None
        logger.info("Prepared artifact %s (%s bytes)", final_name, filesize or "unknown")

        return DownloadArtifact(
            filepath=final_path,
            filename=final_name,
            filesize=filesize,
            workspace=workspace,
        )
    except InvalidURLError:
        shutil.rmtree(workspace, ignore_errors=True)
        raise
    except Exception:
        shutil.rmtree(workspace, ignore_errors=True)
        raise
    finally:
        release_cookiefile(temp_cookie)


def cleanup_artifact(artifact: DownloadArtifact) -> None:
    try:
        shutil.rmtree(artifact.workspace, ignore_errors=True)
        logger.info("Cleaned up workspace %s", artifact.workspace)
    except Exception as exc:
        logger.warning("Failed to clean workspace %s: %s", artifact.workspace, exc)
