class BaseAPIError(Exception):
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
    message = "This video is protected and cannot be downloaded."
    hint = "Try a different video."


class PrivateVideoError(BaseAPIError):
    status_code = 403
    error = "PRIVATE_VIDEO"
    message = "This video is private."
    hint = "Only the owner can access this video."


class AgeRestrictedError(BaseAPIError):
    status_code = 403
    error = "AGE_RESTRICTED"
    message = "This video is age-restricted."
    hint = "Sign in on YouTube to view this content."


class LiveStreamError(BaseAPIError):
    status_code = 400
    error = "LIVE_STREAM"
    message = "Live streams cannot be downloaded."
    hint = "Wait until the stream ends."


class GeoBlockedError(BaseAPIError):
    status_code = 403
    error = "GEO_BLOCKED"
    message = "This video is not available in your region."
    hint = "Try using a VPN."


class NetworkError(BaseAPIError):
    status_code = 503
    error = "NETWORK_ERROR"
    message = "Could not reach YouTube."
    hint = "Check your internet connection."


class ExtractionError(BaseAPIError):
    status_code = 500
    error = "EXTRACTION_ERROR"
    message = "Failed to extract video data."
    hint = "YouTube may have changed. Try again later."


def classify_ytdlp_error(error_str: str) -> BaseAPIError:
    e = error_str.lower()
    
    if any(k in e for k in ["drm", "protected", "widevine"]):
        return DRMError()
    if any(k in e for k in ["private video", "video is private"]):
        return PrivateVideoError()
    if any(k in e for k in ["age", "sign in to confirm", "age-restricted"]):
        return AgeRestrictedError()
    if any(k in e for k in ["nsig", "signature", "cipher"]):
        return ExtractionError(hint="Update yt-dlp: pip install -U yt-dlp")
    if any(k in e for k in ["not available in your country", "geo", "blocked"]):
        return GeoBlockedError()
    if any(k in e for k in ["live stream", "is live"]):
        return LiveStreamError()
    if any(k in e for k in ["network", "connection", "timeout"]):
        return NetworkError()
    if any(k in e for k in ["invalid url", "unsupported url"]):
        return InvalidURLError()
    
    return DownloadError(message=f"Download failed: {error_str[:100]}")
