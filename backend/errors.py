"""
Error Handling Module - Phase 6
Custom exceptions and error handlers for better API responses
"""

import logging
import traceback
from datetime import datetime
from functools import wraps
from typing import Optional, Callable, Any

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse


# ==========================================
# Configure Logging
# ==========================================

# Create logger
logger = logging.getLogger("youtube_downloader")
logger.setLevel(logging.DEBUG)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_format = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
console_handler.setFormatter(console_format)
logger.addHandler(console_handler)

# File handler for errors
try:
    import os
    log_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    file_handler = logging.FileHandler(
        os.path.join(log_dir, 'error.log'),
        encoding='utf-8'
    )
    file_handler.setLevel(logging.ERROR)
    file_format = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_format)
    logger.addHandler(file_handler)
except Exception as e:
    print(f"Warning: Could not create file logger: {e}")


# ==========================================
# Custom Exceptions
# ==========================================

class AppException(Exception):
    """Base application exception"""
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: str = "INTERNAL_ERROR",
        details: Optional[dict] = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        super().__init__(message)


class ValidationError(AppException):
    """Validation error for invalid input"""
    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(
            message=message,
            status_code=400,
            error_code="VALIDATION_ERROR",
            details={"field": field} if field else {}
        )


class URLValidationError(ValidationError):
    """Invalid YouTube URL"""
    def __init__(self, url: str):
        super().__init__(
            message="Invalid YouTube URL. Please provide a valid YouTube video or playlist URL.",
            field="url"
        )
        self.details["provided_url"] = url[:100]  # Truncate for safety


class VideoNotFoundError(AppException):
    """Video not found or unavailable"""
    def __init__(self, video_id: Optional[str] = None):
        super().__init__(
            message="Video not found or unavailable. It may be private, deleted, or region-restricted.",
            status_code=404,
            error_code="VIDEO_NOT_FOUND",
            details={"video_id": video_id} if video_id else {}
        )


class DownloadError(AppException):
    """Error during download process"""
    def __init__(self, message: str, original_error: Optional[str] = None):
        super().__init__(
            message=message,
            status_code=500,
            error_code="DOWNLOAD_ERROR",
            details={"original_error": original_error} if original_error else {}
        )


class FileSizeExceededError(AppException):
    """File size exceeds limit"""
    def __init__(self, file_size_mb: float, max_size_mb: int):
        super().__init__(
            message=f"File size ({file_size_mb:.1f}MB) exceeds the maximum allowed ({max_size_mb}MB). Try a lower quality.",
            status_code=413,
            error_code="FILE_TOO_LARGE",
            details={
                "file_size_mb": file_size_mb,
                "max_size_mb": max_size_mb
            }
        )


class DurationExceededError(AppException):
    """Video duration exceeds limit"""
    def __init__(self, duration_minutes: float, max_minutes: int):
        super().__init__(
            message=f"Video duration ({duration_minutes:.0f} min) exceeds the maximum allowed ({max_minutes} min).",
            status_code=413,
            error_code="DURATION_TOO_LONG",
            details={
                "duration_minutes": duration_minutes,
                "max_minutes": max_minutes
            }
        )


class RateLimitError(AppException):
    """Rate limit exceeded"""
    def __init__(self, retry_after: int = 60):
        super().__init__(
            message="Too many requests. Please wait before trying again.",
            status_code=429,
            error_code="RATE_LIMIT_EXCEEDED",
            details={"retry_after_seconds": retry_after}
        )


class TaskNotFoundError(AppException):
    """Download task not found"""
    def __init__(self, task_id: str):
        super().__init__(
            message=f"Download task '{task_id}' not found.",
            status_code=404,
            error_code="TASK_NOT_FOUND",
            details={"task_id": task_id}
        )


class ConversionError(AppException):
    """Error during format conversion"""
    def __init__(self, message: str, output_format: Optional[str] = None):
        super().__init__(
            message=message,
            status_code=500,
            error_code="CONVERSION_ERROR",
            details={"output_format": output_format} if output_format else {}
        )


class ServiceUnavailableError(AppException):
    """External service unavailable"""
    def __init__(self, service: str = "YouTube"):
        super().__init__(
            message=f"{service} is temporarily unavailable. Please try again later.",
            status_code=503,
            error_code="SERVICE_UNAVAILABLE",
            details={"service": service}
        )


# ==========================================
# Error Response Builder
# ==========================================

def build_error_response(
    message: str,
    status_code: int,
    error_code: str,
    details: Optional[dict] = None,
    request_id: Optional[str] = None
) -> dict:
    """Build a standardized error response"""
    response = {
        "success": False,
        "error": {
            "code": error_code,
            "message": message,
            "status": status_code,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    }
    
    if details:
        response["error"]["details"] = details
    
    if request_id:
        response["error"]["request_id"] = request_id
    
    return response


# ==========================================
# Exception Handlers
# ==========================================

async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Handle custom application exceptions"""
    # Log the error
    logger.error(
        f"{exc.error_code}: {exc.message}",
        extra={
            "status_code": exc.status_code,
            "path": str(request.url),
            "method": request.method,
            "details": exc.details
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=build_error_response(
            message=exc.message,
            status_code=exc.status_code,
            error_code=exc.error_code,
            details=exc.details
        )
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle FastAPI HTTP exceptions"""
    error_code = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
        422: "VALIDATION_ERROR",
        429: "TOO_MANY_REQUESTS",
        500: "INTERNAL_ERROR",
        502: "BAD_GATEWAY",
        503: "SERVICE_UNAVAILABLE"
    }.get(exc.status_code, "HTTP_ERROR")
    
    return JSONResponse(
        status_code=exc.status_code,
        content=build_error_response(
            message=str(exc.detail),
            status_code=exc.status_code,
            error_code=error_code
        )
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions"""
    # Log the full traceback for debugging
    logger.error(
        f"Unhandled exception: {str(exc)}",
        exc_info=True,
        extra={
            "path": str(request.url),
            "method": request.method,
            "traceback": traceback.format_exc()
        }
    )
    
    # Return generic error message to user
    return JSONResponse(
        status_code=500,
        content=build_error_response(
            message="An unexpected error occurred. Please try again later.",
            status_code=500,
            error_code="INTERNAL_ERROR"
        )
    )


# ==========================================
# Decorator for Error Handling
# ==========================================

def handle_errors(func: Callable) -> Callable:
    """Decorator to handle errors in route handlers"""
    @wraps(func)
    async def wrapper(*args, **kwargs) -> Any:
        try:
            return await func(*args, **kwargs)
        except AppException:
            raise  # Re-raise app exceptions to be handled by exception handlers
        except HTTPException:
            raise  # Re-raise HTTP exceptions
        except Exception as e:
            logger.error(
                f"Error in {func.__name__}: {str(e)}",
                exc_info=True
            )
            raise DownloadError(
                message="An error occurred while processing your request.",
                original_error=str(e)
            )
    
    return wrapper


# ==========================================
# Helper Functions
# ==========================================

def log_info(message: str, **kwargs):
    """Log info message"""
    logger.info(message, extra=kwargs)


def log_warning(message: str, **kwargs):
    """Log warning message"""
    logger.warning(message, extra=kwargs)


def log_error(message: str, exc: Optional[Exception] = None, **kwargs):
    """Log error message"""
    logger.error(message, exc_info=exc is not None, extra=kwargs)


def log_debug(message: str, **kwargs):
    """Log debug message"""
    logger.debug(message, extra=kwargs)
