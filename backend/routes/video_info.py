"""
Video information endpoints
"""

from fastapi import APIRouter, HTTPException
from typing import Optional
import yt_dlp

from ..models import VideoInfoRequest, VideoInfo, PlaylistInfo, FormatInfo
from ..config import settings

router = APIRouter()


def format_duration(seconds: Optional[int]) -> Optional[str]:
    """Format duration in seconds to HH:MM:SS"""
    if not seconds:
        return None
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def format_views(views: Optional[int]) -> Optional[str]:
    """Format view count"""
    if not views:
        return None
    if views >= 1_000_000_000:
        return f"{views / 1_000_000_000:.1f}B"
    if views >= 1_000_000:
        return f"{views / 1_000_000:.1f}M"
    if views >= 1_000:
        return f"{views / 1_000:.1f}K"
    return str(views)


def is_playlist_url(url: str) -> bool:
    """Check if URL is a playlist"""
    return 'list=' in url or '/playlist?' in url


@router.post("/info", response_model=VideoInfo | PlaylistInfo)
async def get_video_info(request: VideoInfoRequest):
    """
    Get information about a YouTube video or playlist
    """
    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': 'in_playlist' if is_playlist_url(request.url) else False,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(request.url, download=False)
        
        # Handle playlist
        if info.get('_type') == 'playlist' or 'entries' in info:
            entries = info.get('entries', [])
            videos = []
            for i, entry in enumerate(entries):
                if entry:
                    videos.append({
                        'index': i + 1,
                        'id': entry.get('id', ''),
                        'title': entry.get('title', f'Video {i + 1}'),
                        'duration': entry.get('duration'),
                        'url': entry.get('url') or entry.get('webpage_url') or f"https://www.youtube.com/watch?v={entry.get('id', '')}"
                    })
            
            return PlaylistInfo(
                id=info.get('id', ''),
                title=info.get('title', 'Unknown Playlist'),
                description=info.get('description'),
                channel=info.get('uploader') or info.get('channel'),
                video_count=len(videos),
                videos=videos
            )
        
        # Handle single video
        formats = []
        seen_resolutions = set()
        
        for fmt in info.get('formats', []):
            if fmt.get('vcodec') != 'none':  # Video formats only
                resolution = fmt.get('resolution', 'N/A')
                if resolution not in seen_resolutions:
                    seen_resolutions.add(resolution)
                    formats.append(FormatInfo(
                        format_id=fmt.get('format_id', 'N/A'),
                        resolution=resolution,
                        extension=fmt.get('ext', 'N/A'),
                        filesize=fmt.get('filesize'),
                        filesize_approx=fmt.get('filesize_approx'),
                        fps=fmt.get('fps'),
                        vcodec=fmt.get('vcodec'),
                        acodec=fmt.get('acodec')
                    ))
        
        # Sort formats by resolution (descending)
        formats.sort(key=lambda x: int(x.resolution.replace('p', '').split('x')[-1]) if x.resolution and x.resolution.replace('p', '').split('x')[-1].isdigit() else 0, reverse=True)
        
        return VideoInfo(
            id=info.get('id', ''),
            title=info.get('title', 'Unknown'),
            description=info.get('description'),
            duration=info.get('duration'),
            duration_formatted=format_duration(info.get('duration')),
            thumbnail=info.get('thumbnail'),
            channel=info.get('uploader') or info.get('channel'),
            channel_url=info.get('uploader_url') or info.get('channel_url'),
            view_count=info.get('view_count'),
            view_count_formatted=format_views(info.get('view_count')),
            upload_date=info.get('upload_date'),
            formats=formats[:15],  # Limit to 15 formats
            is_playlist=False
        )
        
    except yt_dlp.utils.DownloadError as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch video info: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.get("/formats/{video_id}")
async def get_video_formats(video_id: str):
    """
    Get available formats for a video by ID
    """
    url = f"https://www.youtube.com/watch?v={video_id}"
    request = VideoInfoRequest(url=url)
    return await get_video_info(request)
