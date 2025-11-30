# Worker package
import os
import sys

# Add parent directory to path for imports
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from .download_manager import DownloadManager
from .ytdlp_downloader import YTDLPDownloader, downloader, DownloadError, MetadataError

# Global download manager instance
download_manager = DownloadManager()

__all__ = [
    'DownloadManager',
    'download_manager',
    'YTDLPDownloader',
    'downloader',
    'DownloadError',
    'MetadataError',
]
