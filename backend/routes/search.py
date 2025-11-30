"""
Search and Subtitles endpoints - Phase 8 & 10
Includes: /search, /subtitles
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
import yt_dlp
import asyncio
from functools import lru_cache
import time
import json
import os
from pathlib import Path

from ..config import settings

router = APIRouter()


# ============== Metadata Cache ==============
# Simple in-memory cache with TTL

class MetadataCache:
    """Simple in-memory cache for video metadata"""
    
    def __init__(self, ttl_seconds: int = 3600):
        self._cache = {}
        self._ttl = ttl_seconds
    
    def get(self, key: str):
        if key in self._cache:
            data, timestamp = self._cache[key]
            if time.time() - timestamp < self._ttl:
                return data
            else:
                del self._cache[key]
        return None
    
    def set(self, key: str, value):
        self._cache[key] = (value, time.time())
    
    def clear_expired(self):
        current_time = time.time()
        expired_keys = [
            key for key, (_, timestamp) in self._cache.items()
            if current_time - timestamp >= self._ttl
        ]
        for key in expired_keys:
            del self._cache[key]


# Global cache instance (1 hour TTL)
metadata_cache = MetadataCache(ttl_seconds=3600)


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


# ============== YouTube Search Endpoint ==============

@router.get("/search")
async def search_youtube(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(10, ge=1, le=25, description="Max results")
):
    """
    GET /search?q=<query>&limit=<n>
    
    Search YouTube videos using yt-dlp (no API key required).
    Uses ytsearch feature to find videos.
    
    Returns list of video results with:
    - title, channel, duration
    - thumbnail, view count
    - video URL
    """
    # Check cache first
    cache_key = f"search:{q}:{limit}"
    cached = metadata_cache.get(cache_key)
    if cached:
        return cached
    
    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
            'skip_download': True,
        }
        
        # Use ytsearch to search YouTube
        search_query = f"ytsearch{limit}:{q}"
        
        def extract_info():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                return ydl.extract_info(search_query, download=False)
        
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        info = await loop.run_in_executor(None, extract_info)
        
        if not info or 'entries' not in info:
            return []
        
        results = []
        for entry in info.get('entries', []):
            if not entry:
                continue
            
            result = {
                'id': entry.get('id'),
                'title': entry.get('title'),
                'url': f"https://www.youtube.com/watch?v={entry.get('id')}",
                'channel': entry.get('channel') or entry.get('uploader'),
                'duration': entry.get('duration'),
                'duration_formatted': format_duration(entry.get('duration')),
                'thumbnail': entry.get('thumbnail') or f"https://i.ytimg.com/vi/{entry.get('id')}/hqdefault.jpg",
                'view_count': entry.get('view_count'),
                'view_count_formatted': format_views(entry.get('view_count')),
            }
            results.append(result)
        
        # Cache results
        metadata_cache.set(cache_key, results)
        
        return results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


# ============== Subtitles Endpoints ==============

@router.get("/subtitles")
async def get_subtitles(
    url: str = Query(..., description="YouTube video URL")
):
    """
    GET /subtitles?url=<youtube_url>
    
    Get available subtitle languages for a video.
    Returns list of available subtitle tracks.
    """
    # Check cache
    cache_key = f"subtitles:{url}"
    cached = metadata_cache.get(cache_key)
    if cached:
        return cached
    
    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'skip_download': True,
            'writesubtitles': True,
            'writeautomaticsub': True,
            'subtitleslangs': ['all'],
        }
        
        def extract_info():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                return ydl.extract_info(url, download=False)
        
        loop = asyncio.get_event_loop()
        info = await loop.run_in_executor(None, extract_info)
        
        if not info:
            raise HTTPException(status_code=404, detail="Video not found")
        
        subtitles = []
        
        # Manual subtitles
        manual_subs = info.get('subtitles', {})
        for lang, formats in manual_subs.items():
            subtitles.append({
                'lang': lang,
                'name': get_language_name(lang),
                'type': 'manual',
                'formats': [f.get('ext', 'unknown') for f in formats] if formats else []
            })
        
        # Auto-generated subtitles
        auto_subs = info.get('automatic_captions', {})
        for lang, formats in auto_subs.items():
            # Skip if already have manual version
            if lang not in manual_subs:
                subtitles.append({
                    'lang': lang,
                    'name': get_language_name(lang) + ' (auto)',
                    'type': 'auto',
                    'formats': [f.get('ext', 'unknown') for f in formats] if formats else []
                })
        
        result = {
            'video_id': info.get('id'),
            'title': info.get('title'),
            'subtitles': subtitles,
            'has_subtitles': len(subtitles) > 0
        }
        
        # Cache results
        metadata_cache.set(cache_key, result)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get subtitles: {str(e)}")


@router.post("/subtitles/download")
async def download_with_subtitles(
    url: str,
    lang: str,
    embed: bool = False,
    format: str = "mp4",
    quality: str = "best"
):
    """
    POST /subtitles/download
    
    Download video with subtitles.
    Can optionally embed subtitles into the video file.
    """
    from ..worker import download_manager
    
    try:
        # Add download with subtitle options
        task_id = await download_manager.add_download(
            url=url,
            format=format,
            quality=quality,
            audio_only=False,
            subtitle_lang=lang,
            embed_subtitles=embed
        )
        
        return {
            'task_id': task_id,
            'message': f"Download queued with {lang} subtitles",
            'embed_subtitles': embed
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start download: {str(e)}")


# ============== Cached Metadata Endpoint ==============

@router.get("/metadata/cached")
async def get_cached_metadata(
    url: str = Query(..., description="YouTube video URL")
):
    """
    GET /metadata/cached?url=<youtube_url>
    
    Get video metadata with caching (1 hour TTL).
    Much faster for repeated requests.
    """
    # Check cache
    cache_key = f"metadata:{url}"
    cached = metadata_cache.get(cache_key)
    if cached:
        return {**cached, 'cached': True}
    
    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
        }
        
        def extract_info():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                return ydl.extract_info(url, download=False)
        
        loop = asyncio.get_event_loop()
        info = await loop.run_in_executor(None, extract_info)
        
        if not info:
            raise HTTPException(status_code=404, detail="Video not found")
        
        result = {
            'id': info.get('id'),
            'title': info.get('title'),
            'description': info.get('description', '')[:500],
            'thumbnail': info.get('thumbnail'),
            'duration': info.get('duration'),
            'duration_formatted': format_duration(info.get('duration')),
            'channel': info.get('channel') or info.get('uploader'),
            'view_count': info.get('view_count'),
            'view_count_formatted': format_views(info.get('view_count')),
            'upload_date': info.get('upload_date'),
            'cached': False
        }
        
        # Cache results
        metadata_cache.set(cache_key, result)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get metadata: {str(e)}")


# ============== Cache Management ==============

@router.delete("/cache/clear")
async def clear_metadata_cache():
    """
    DELETE /cache/clear
    
    Clear the metadata cache (admin endpoint).
    """
    metadata_cache._cache.clear()
    return {'message': 'Cache cleared', 'success': True}


@router.get("/cache/stats")
async def get_cache_stats():
    """
    GET /cache/stats
    
    Get cache statistics.
    """
    metadata_cache.clear_expired()
    return {
        'entries': len(metadata_cache._cache),
        'ttl_seconds': metadata_cache._ttl
    }


# ============== Language Name Helper ==============

def get_language_name(lang_code: str) -> str:
    """Get human-readable language name from code"""
    language_names = {
        'en': 'English',
        'es': 'Spanish',
        'fr': 'French',
        'de': 'German',
        'it': 'Italian',
        'pt': 'Portuguese',
        'ru': 'Russian',
        'ja': 'Japanese',
        'ko': 'Korean',
        'zh': 'Chinese',
        'zh-Hans': 'Chinese (Simplified)',
        'zh-Hant': 'Chinese (Traditional)',
        'ar': 'Arabic',
        'hi': 'Hindi',
        'th': 'Thai',
        'vi': 'Vietnamese',
        'id': 'Indonesian',
        'ms': 'Malay',
        'nl': 'Dutch',
        'pl': 'Polish',
        'tr': 'Turkish',
        'sv': 'Swedish',
        'no': 'Norwegian',
        'da': 'Danish',
        'fi': 'Finnish',
        'cs': 'Czech',
        'el': 'Greek',
        'he': 'Hebrew',
        'hu': 'Hungarian',
        'ro': 'Romanian',
        'uk': 'Ukrainian',
    }
    return language_names.get(lang_code, lang_code.upper())
