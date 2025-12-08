"""
Custom exceptions for YouTube downloader
"""


class DownloaderError(Exception):
    """Base exception for downloader errors"""
    pass


class InvalidURLError(DownloaderError):
    """Invalid YouTube URL"""
    pass


class NoMP4FormatsError(DownloaderError):
    """No MP4 formats available"""
    pass


class DRMProtectedError(DownloaderError):
    """Video is DRM protected"""
    pass


class VideoUnavailableError(DownloaderError):
    """Video is unavailable or removed"""
    pass


class NetworkError(DownloaderError):
    """Network connection issue"""
    pass


class InvalidPathError(DownloaderError):
    """Invalid download folder path"""
    pass
