# Custom Exceptions for YouTube Downloader API

class BaseAPIError(Exception):
    """Base exception for all API errors"""
    status_code: int = 500
    error: str = "INTERNAL_ERROR"
    message: str = "An unexpected error occurred."
    hint: str = "Please try again later."

    def __init__(self, message: str = None, hint: str = None):
        if message:
            self.message = message
        if hint:
            self.hint = hint
        super().__init__(self.message)


class InvalidURLError(BaseAPIError):
    status_code = 400
    error = "INVALID_URL"
    message = "Please enter a valid YouTube link."
    hint = "Example: https://youtu.be/xxxx or https://www.youtube.com/watch?v=xxxx"


class MetadataError(BaseAPIError):
    status_code = 400
    error = "METADATA_ERROR"
    message = "Could not fetch video information."
    hint = "Make sure the video exists and is publicly available."


class DownloadError(BaseAPIError):
    status_code = 500
    error = "DOWNLOAD_ERROR"
    message = "Failed to download the video."
    hint = "Try again or select a different quality."


class DRMError(BaseAPIError):
    status_code = 403
    error = "DRM_PROTECTED"
    message = "This video is protected by DRM and cannot be downloaded."
    hint = "Try downloading a non-DRM normal YouTube video."


class PrivateVideoError(BaseAPIError):
    status_code = 403
    error = "PRIVATE_VIDEO"
    message = "This video is private and cannot be downloaded."
    hint = "Only the owner can access this video."


class AgeRestrictedError(BaseAPIError):
    status_code = 403
    error = "AGE_RESTRICTED"
    message = "This video is age-restricted."
    hint = "You must sign in on YouTube to view this content."


class UnavailableQualityError(BaseAPIError):
    status_code = 400
    error = "QUALITY_UNAVAILABLE"
    message = "The selected quality is not available for this video."
    hint = "Try 720p or a lower resolution."


class ExtractionError(BaseAPIError):
    status_code = 500
    error = "EXTRACTION_ERROR"
    message = "Failed to extract video data from YouTube."
    hint = "YouTube may have changed its format. Try again later."


class YTDLPError(BaseAPIError):
    status_code = 500
    error = "YTDLP_OUTDATED"
    message = "YouTube encryption changed recently."
    hint = "Update yt-dlp to the latest version: pip install -U yt-dlp"


class NetworkError(BaseAPIError):
    status_code = 503
    error = "NETWORK_ERROR"
    message = "Could not reach YouTube."
    hint = "Check your internet connection and try again."


class LiveStreamError(BaseAPIError):
    status_code = 400
    error = "LIVE_STREAM"
    message = "Live streams cannot be downloaded."
    hint = "Wait until the stream ends and try again."


class GeoBlockedError(BaseAPIError):
    status_code = 403
    error = "GEO_BLOCKED"
    message = "This video is not available in your region."
    hint = "Try using a VPN or find another video."


def classify_ytdlp_error(error_str: str) -> BaseAPIError:
    """
    Analyze yt-dlp error message and return the appropriate exception.
    """
    error_lower = error_str.lower()
    
    # DRM / Protected content
    if any(kw in error_lower for kw in ["drm", "protected", "widevine", "playready"]):
        return DRMError()
    
    # Private video
    if any(kw in error_lower for kw in ["private video", "video is private", "this video is private"]):
        return PrivateVideoError()
    
    # Age restricted
    if any(kw in error_lower for kw in ["age", "sign in to confirm", "confirm your age", "age-restricted"]):
        return AgeRestrictedError()
    
    # nsig / signature extraction (yt-dlp needs update)
    if any(kw in error_lower for kw in ["nsig", "signature", "cipher", "n parameter"]):
        return YTDLPError()
    
    # No formats available
    if any(kw in error_lower for kw in ["no video formats", "requested format not available", "format is not available"]):
        return UnavailableQualityError()
    
    # SABR / unplayable
    if any(kw in error_lower for kw in ["sabr", "unplayable", "playability"]):
        return DRMError()
    
    # Geo-blocked
    if any(kw in error_lower for kw in ["not available in your country", "geo", "blocked", "unavailable in your region"]):
        return GeoBlockedError()
    
    # Live stream
    if any(kw in error_lower for kw in ["live stream", "is live", "live event"]):
        return LiveStreamError()
    
    # Network errors
    if any(kw in error_lower for kw in ["network", "connection", "timeout", "unreachable", "getaddrinfo"]):
        return NetworkError()
    
    # Invalid URL
    if any(kw in error_lower for kw in ["invalid url", "unsupported url", "no video id"]):
        return InvalidURLError()
    
    # Generic extraction error
    if any(kw in error_lower for kw in ["extract", "unable to extract"]):
        return ExtractionError()
    
    # Default to generic download error
    return DownloadError(message=f"Download failed: {error_str[:100]}")
