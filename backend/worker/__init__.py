# Worker package
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
