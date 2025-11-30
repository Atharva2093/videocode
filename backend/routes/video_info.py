"""
Video information endpoints - Phase 2
Includes: /metadata, /playlist, /thumbnail
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse, Response
from typing import Optional
import yt_dlp
import httpx
import io

from ..models import (
    VideoInfoRequest, VideoInfo, PlaylistInfo, FormatInfo,
    MetadataResponse, PlaylistResponse, PlaylistVideoItem
)
from ..config import settings

router = APIRouter()


# ============== Helper Functions ==============

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


def format_filesize(size: Optional[int]) -> Optional[str]:
    """Format filesize in bytes to human readable"""
    if not size:
        return None
    if size >= 1073741824:
        return f"{size / 1073741824:.2f} GB"
    if size >= 1048576:
        return f"{size / 1048576:.2f} MB"
    if size >= 1024:
        return f"{size / 1024:.2f} KB"
    return f"{size} B"


def is_playlist_url(url: str) -> bool:
    """Check if URL is a playlist"""
    return 'list=' in url or '/playlist?' in url


def extract_video_id(url: str) -> Optional[str]:
    """Extract video ID from YouTube URL"""
    import re
    patterns = [
        r'(?:youtube\.com\/watch\?v=)([\w-]+)',
        r'(?:youtube\.com\/shorts\/)([\w-]+)',
        r'(?:youtu\.be\/)([\w-]+)',
        r'(?:youtube\.com\/embed\/)([\w-]+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


# ============== Main Endpoints ==============

@router.get("/metadata")
async def get_metadata(url: str = Query(..., description="YouTube video URL")):
    """
    GET /metadata?url=<youtube_url>
    
    Returns comprehensive video metadata including:
    - title, duration, thumbnail
    - channel info, view count
    - available formats with file sizes
    """
    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
        
        # Check if it's a playlist - redirect to playlist endpoint
        if info.get('_type') == 'playlist' or 'entries' in info:
            raise HTTPException(
                status_code=400, 
                detail="URL is a playlist. Use /playlist endpoint instead."
            )
        
        # Extract formats with sizes
        formats = []
        seen_resolutions = set()
        total_size = 0
        
        for fmt in info.get('formats', []):
            if fmt.get('vcodec') != 'none':  # Video formats only
                resolution = fmt.get('resolution', 'N/A')
                if resolution not in seen_resolutions:
                    seen_resolutions.add(resolution)
                    
                    size = fmt.get('filesize') or fmt.get('filesize_approx')
                    if size and total_size == 0:
                        total_size = size  # Use first available size as estimate
                    
                    formats.append(FormatInfo(
                        format_id=fmt.get('format_id', 'N/A'),
                        resolution=resolution,
                        extension=fmt.get('ext', 'N/A'),
                        filesize=fmt.get('filesize'),
                        filesize_approx=fmt.get('filesize_approx'),
                        filesize_formatted=format_filesize(fmt.get('filesize') or fmt.get('filesize_approx')),
                        fps=fmt.get('fps'),
                        vcodec=fmt.get('vcodec'),
                        acodec=fmt.get('acodec'),
                        bitrate=fmt.get('tbr')
                    ))
        
        # Sort formats by resolution (descending)
        formats.sort(
            key=lambda x: int(x.resolution.replace('p', '').split('x')[-1]) 
            if x.resolution and x.resolution.replace('p', '').split('x')[-1].isdigit() 
            else 0, 
            reverse=True
        )
        
        return MetadataResponse(
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
            like_count=info.get('like_count'),
            upload_date=info.get('upload_date'),
            formats=formats[:20],  # Limit to 20 formats
            total_size_approx=total_size,
            total_size_formatted=format_filesize(total_size)
        )
        
    except yt_dlp.utils.DownloadError as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch metadata: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.get("/playlist")
async def get_playlist(url: str = Query(..., description="YouTube playlist URL")):
    """
    GET /playlist?url=<playlist_url>
    
    Returns playlist information including:
    - playlist name, description, channel
    - list of all video titles and IDs
    - total duration
    """
    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,  # Don't download video info, just list
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
        
        # Verify it's a playlist
        if info.get('_type') != 'playlist' and 'entries' not in info:
            raise HTTPException(
                status_code=400, 
                detail="URL is not a playlist. Use /metadata endpoint for single videos."
            )
        
        entries = info.get('entries', [])
        videos = []
        total_duration = 0
        
        for i, entry in enumerate(entries):
            if entry:
                duration = entry.get('duration')
                if duration:
                    total_duration += duration
                
                video_id = entry.get('id', '')
                videos.append(PlaylistVideoItem(
                    index=i + 1,
                    id=video_id,
                    title=entry.get('title', f'Video {i + 1}'),
                    duration=duration,
                    duration_formatted=format_duration(duration),
                    thumbnail=entry.get('thumbnail') or f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg" if video_id else None,
                    url=entry.get('url') or entry.get('webpage_url') or f"https://www.youtube.com/watch?v={video_id}"
                ))
        
        return PlaylistResponse(
            id=info.get('id', ''),
            title=info.get('title', 'Unknown Playlist'),
            description=info.get('description'),
            channel=info.get('uploader') or info.get('channel'),
            channel_url=info.get('uploader_url') or info.get('channel_url'),
            video_count=len(videos),
            total_duration=total_duration if total_duration > 0 else None,
            total_duration_formatted=format_duration(total_duration) if total_duration > 0 else None,
            thumbnail=info.get('thumbnail'),
            videos=videos
        )
        
    except yt_dlp.utils.DownloadError as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch playlist: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.get("/thumbnail")
async def get_thumbnail(
    url: str = Query(..., description="YouTube video URL"),
    quality: str = Query("hq", description="Thumbnail quality: sd, mq, hq, maxres")
):
    """
    GET /thumbnail?url=<video_url>&quality=hq
    
    Returns the video thumbnail as an image.
    Quality options: sd (120x90), mq (320x180), hq (480x360), maxres (1280x720)
    """
    try:
        # Extract video ID
        video_id = extract_video_id(url)
        
        if not video_id:
            # Try to get thumbnail from yt-dlp
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                thumbnail_url = info.get('thumbnail')
                if not thumbnail_url:
                    raise HTTPException(status_code=404, detail="Thumbnail not found")
        else:
            # Construct thumbnail URL based on quality
            quality_map = {
                'sd': 'sddefault',
                'mq': 'mqdefault', 
                'hq': 'hqdefault',
                'maxres': 'maxresdefault'
            }
            quality_suffix = quality_map.get(quality, 'hqdefault')
            thumbnail_url = f"https://i.ytimg.com/vi/{video_id}/{quality_suffix}.jpg"
        
        # Fetch the thumbnail image
        async with httpx.AsyncClient() as client:
            response = await client.get(thumbnail_url, follow_redirects=True)
            
            if response.status_code != 200:
                # Try fallback to hqdefault
                if video_id:
                    thumbnail_url = f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"
                    response = await client.get(thumbnail_url, follow_redirects=True)
                
                if response.status_code != 200:
                    raise HTTPException(status_code=404, detail="Thumbnail not found")
            
            # Return image as streaming response
            return Response(
                content=response.content,
                media_type="image/jpeg",
                headers={
                    "Content-Disposition": f"inline; filename={video_id or 'thumbnail'}.jpg",
                    "Cache-Control": "public, max-age=86400"  # Cache for 24 hours
                }
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch thumbnail: {str(e)}")


# ============== Legacy Endpoints (Backward Compatibility) ==============

@router.post("/info", response_model=VideoInfo | PlaylistInfo)
async def get_video_info(request: VideoInfoRequest):
    """
    POST /info - Legacy endpoint for video/playlist info
    Kept for backward compatibility with existing frontend
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
            if fmt.get('vcodec') != 'none':
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
        
        formats.sort(
            key=lambda x: int(x.resolution.replace('p', '').split('x')[-1]) 
            if x.resolution and x.resolution.replace('p', '').split('x')[-1].isdigit() 
            else 0, 
            reverse=True
        )
        
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
            formats=formats[:15],
            is_playlist=False
        )
        
    except yt_dlp.utils.DownloadError as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch video info: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.get("/formats/{video_id}")
async def get_video_formats(video_id: str):
    """
    GET /formats/{video_id} - Get available formats for a video by ID
    """
    url = f"https://www.youtube.com/watch?v={video_id}"
    return await get_metadata(url=url)
        
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
