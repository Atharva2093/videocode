import logging
import os
import re
import shutil
import tempfile
import time
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional

import yt_dlp

from exceptions import InvalidURLError

logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
COOKIES_FILE = os.path.join(BACKEND_DIR, "cookies.txt")

# Render / K8s secret path (read-only) — keep this path but copy into writable temp before use
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


def cleanup_stale_workspaces(max_age_hours: int = 6) -> None:
    tmp_dir = tempfile.gettempdir()
    now = time.time()
    max_age = max_age_hours * 3600
    removed = 0

    try:
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
    except Exception:
        # non-fatal if tmp listing fails
        pass

    if removed:
        logger.info("Removed %s stale workspaces", removed)


def prepare_cookie_jar(dest_dir: Optional[str] = None) -> Optional[str]:
    """
    Copy the read-only cookies file to a writable location.
    Returns path to the writable cookiefile or None if not available.
    """
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
            # ignore if not supported on platform
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


def _build_format_selector(format_id: str) -> str:
    if format_id and format_id != "best":
        return f"{format_id}+bestaudio/{format_id}/bestvideo+bestaudio/best"
    return "bestvideo+bestaudio/best"


def _is_supported_mp4_format(entry: Dict) -> bool:
    if not entry or entry.get("has_drm"):
        return False
    if not entry.get("url"):
        return False
    if entry.get("ext") != "mp4":
        return False
    if entry.get("vcodec", "none") in ("none", None):
        return False
    if not entry.get("height"):
        return False

    format_note = (entry.get("format_note") or "").lower()
    protocol = (entry.get("protocol") or "").lower()

    # exclude webm / dash / hls / segmented protocols that can't be streamed safely without ffmpeg
    if "webm" in format_note:
        return False
    if any(flag in format_note for flag in ("dash", "hls")):
        return False
    if protocol in {"m3u8", "m3u8_native", "dash", "http_dash_segments"}:
        return False

    return True


def filter_supported_formats(formats: Iterable[Dict]) -> List[Dict]:
    filtered = [entry for entry in (formats or []) if _is_supported_mp4_format(entry)]
    # sort highest resolution first
    filtered.sort(key=lambda item: (item.get("height") or 0, item.get("fps") or 0), reverse=True)
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
        "format": _build_format_selector(format_id),
        "merge_output_format": "mp4",
        "no_write_cookie_file": True,
        "cookiesfrombrowser": None,
        "no_cache_dir": True,
        # disable internal cache updates / cookie writes
        "reject_cookies": True,
    }

    if cookiefile:
        ydl_opts["cookiefile"] = cookiefile
        logger.info("Cookies loaded")
    else:
        logger.info("Cookies missing")

    if is_ffmpeg_available():
        ydl_opts["ffmpeg_location"] = get_ffmpeg_location()
    else:
        # prefer progressive mp4s if ffmpeg isn't installed
        logger.warning("FFmpeg not available - falling back to progressive MP4 formats only")
        preferred = format_id if format_id and format_id != "best" else "best"
        ydl_opts["format"] = f"{preferred}[ext=mp4]/best[ext=mp4]/best"
        ydl_opts.pop("merge_output_format", None)

    return ydl_opts


def prepare_download(url: str, format_id: str = "best") -> DownloadArtifact:
    """
    Prepare and perform the download in a temp workspace, returning a DownloadArtifact
    pointing to the final file in that workspace. Caller should stream the file and
    then call cleanup_artifact to remove the workspace.
    """
    cleanup_stale_workspaces(max_age_hours=6)

    workspace = tempfile.mkdtemp(prefix="yt-stream-")
    output_template = os.path.join(workspace, "video.%(ext)s")

    cookiefile = prepare_cookie_jar(dest_dir=workspace)
    ydl_opts = get_ydl_opts(output_template, format_id, cookiefile)

    try:
        # First fetch metadata to validate formats
        with yt_dlp.YoutubeDL({**ydl_opts, "skip_download": True, "socket_timeout": 15}) as ydl:
            info = ydl.extract_info(url, download=False)

        if not info:
            raise RuntimeError("Failed to extract video info")
        if info.get("is_live"):
            raise RuntimeError("Live streams cannot be downloaded")

        valid_formats = filter_supported_formats(info.get("formats", []))
        allowed_ids = {fmt.get("format_id") for fmt in valid_formats if fmt.get("format_id")}
        if format_id and format_id != "best" and format_id not in allowed_ids:
            raise InvalidURLError(message="Invalid or unsupported format ID.")

        # Now perform actual download (this will write into the workspace)
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # extract_info with download=True downloads and returns updated info
            info = ydl.extract_info(url, download=True)

        requested = info.get("requested_downloads") or []
        candidate_path = None

        if requested:
            candidate_path = requested[0].get("filepath")

        if not candidate_path:
            candidate_path = info.get("_filename")

        if not candidate_path or not os.path.exists(candidate_path):
            # fallback: pick any file produced in workspace
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

        # rename/move to nice final filename
        if os.path.normcase(candidate_path) != os.path.normcase(final_path):
            try:
                shutil.move(candidate_path, final_path)
            except Exception:
                # if move fails, try copy+remove
                shutil.copyfile(candidate_path, final_path)
                try:
                    os.remove(candidate_path)
                except Exception:
                    pass

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
    except Exception as exc:
        # ensure workspace cleaned on failure
        logger.exception("Download preparation failed: %s", exc)
        shutil.rmtree(workspace, ignore_errors=True)
        raise
    finally:
        cleanup_cookie_jar(cookiefile)


def cleanup_artifact(artifact: DownloadArtifact) -> None:
    try:
        shutil.rmtree(artifact.workspace, ignore_errors=True)
        logger.info("Cleaned up workspace %s", artifact.workspace)
    except Exception as exc:
        logger.warning("Failed to clean workspace %s: %s", artifact.workspace, exc)
