# API Examples

This document provides practical examples for using the YouTube Downloader API.

## Base URL

```
Production: https://your-domain.com/api
Development: http://localhost:8000/api
```

## Health Check

### Check API Status
```bash
curl -X GET "http://localhost:8000/api/health"
```

**Response:**
```json
{
    "status": "ok",
    "yt_dlp_version": "2024.10.22",
    "ffmpeg_available": true,
    "timestamp": "2024-11-30T12:00:00Z"
}
```

## Video Metadata

### Get Video Information
```bash
curl -X GET "http://localhost:8000/api/metadata?url=https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

**Response:**
```json
{
    "id": "dQw4w9WgXcQ",
    "title": "Rick Astley - Never Gonna Give You Up",
    "description": "The official music video...",
    "thumbnail": "https://i.ytimg.com/vi/dQw4w9WgXcQ/maxresdefault.jpg",
    "duration": 212,
    "duration_formatted": "3:32",
    "channel": "Rick Astley",
    "view_count": 1500000000,
    "view_count_formatted": "1.5B",
    "upload_date": "20091025",
    "formats": [
        {
            "format_id": "137",
            "resolution": "1080p",
            "extension": "mp4",
            "filesize": 52428800,
            "filesize_formatted": "50.00 MB"
        }
    ]
}
```

### Get Playlist Information
```bash
curl -X GET "http://localhost:8000/api/playlist?url=https://www.youtube.com/playlist?list=PLxxx"
```

**Response:**
```json
{
    "title": "My Playlist",
    "channel": "Channel Name",
    "video_count": 25,
    "videos": [
        {
            "id": "video1",
            "title": "Video 1",
            "duration": 180,
            "duration_formatted": "3:00",
            "thumbnail": "https://..."
        }
    ]
}
```

## YouTube Search

### Search Videos (No API Key Required)
```bash
curl -X GET "http://localhost:8000/api/search?q=coding%20tutorial&limit=10"
```

**Response:**
```json
[
    {
        "id": "abc123",
        "title": "Python Tutorial for Beginners",
        "url": "https://www.youtube.com/watch?v=abc123",
        "channel": "Programming with Mosh",
        "duration": 3600,
        "duration_formatted": "1:00:00",
        "thumbnail": "https://i.ytimg.com/vi/abc123/hqdefault.jpg",
        "view_count": 5000000,
        "view_count_formatted": "5M"
    }
]
```

## Downloads

### Queue a Download
```bash
curl -X POST "http://localhost:8000/api/download" \
     -H "Content-Type: application/json" \
     -d '{
         "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
         "format": "mp4",
         "quality": "1080p",
         "audio_only": false
     }'
```

**Response:**
```json
{
    "task_id": "550e8400-e29b-41d4-a716-446655440000",
    "message": "Download queued successfully",
    "status": "queued"
}
```

### Check Download Status
```bash
curl -X GET "http://localhost:8000/api/download/550e8400-e29b-41d4-a716-446655440000"
```

**Response (In Progress):**
```json
{
    "task_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "downloading",
    "progress": 45.5,
    "speed": "2.5MB/s",
    "eta": "00:30",
    "title": "Rick Astley - Never Gonna Give You Up"
}
```

**Response (Completed):**
```json
{
    "task_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "completed",
    "progress": 100,
    "title": "Rick Astley - Never Gonna Give You Up",
    "file_path": "/downloads/rick-astley-never-gonna-give-you-up.mp4",
    "file_size": "52.4 MB"
}
```

### Download the File
```bash
curl -X GET "http://localhost:8000/api/download/550e8400-e29b-41d4-a716-446655440000/file" \
     -o video.mp4
```

### Cancel a Download
```bash
curl -X POST "http://localhost:8000/api/download/cancel" \
     -H "Content-Type: application/json" \
     -d '{"task_id": "550e8400-e29b-41d4-a716-446655440000"}'
```

### Get Queue Status
```bash
curl -X GET "http://localhost:8000/api/queue"
```

**Response:**
```json
{
    "tasks": [
        {
            "task_id": "...",
            "status": "downloading",
            "progress": 45,
            "title": "Video 1"
        },
        {
            "task_id": "...",
            "status": "queued",
            "title": "Video 2"
        }
    ],
    "active_count": 1,
    "queued_count": 1,
    "completed_count": 5
}
```

## Subtitles

### Get Available Subtitles
```bash
curl -X GET "http://localhost:8000/api/subtitles?url=https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

**Response:**
```json
{
    "video_id": "dQw4w9WgXcQ",
    "title": "Rick Astley - Never Gonna Give You Up",
    "has_subtitles": true,
    "subtitles": [
        {
            "lang": "en",
            "name": "English",
            "type": "manual",
            "formats": ["vtt", "srv3", "ttml"]
        },
        {
            "lang": "es",
            "name": "Spanish (auto)",
            "type": "auto",
            "formats": ["vtt"]
        }
    ]
}
```

### Download with Subtitles
```bash
curl -X POST "http://localhost:8000/api/subtitles/download" \
     -H "Content-Type: application/json" \
     -d '{
         "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
         "lang": "en",
         "embed": true,
         "format": "mp4",
         "quality": "1080p"
     }'
```

## Mobile Compression

### Download Mobile-Optimized Video
```bash
curl -X POST "http://localhost:8000/api/mobile-compression" \
     -H "Content-Type: application/json" \
     -d '{
         "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
         "audio_only": false,
         "max_resolution": "480p"
     }' \
     -o video_mobile.mp4
```

### Download Small Audio (64kbps MP3)
```bash
curl -X POST "http://localhost:8000/api/mobile-compression" \
     -H "Content-Type: application/json" \
     -d '{
         "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
         "audio_only": true
     }' \
     -o audio.mp3
```

## Cache Management

### Get Cache Statistics
```bash
curl -X GET "http://localhost:8000/api/cache/stats"
```

**Response:**
```json
{
    "entries": 42,
    "ttl_seconds": 3600
}
```

### Clear Cache
```bash
curl -X DELETE "http://localhost:8000/api/cache/clear"
```

## Error Responses

### Rate Limit Exceeded
```json
{
    "detail": "Too many requests. Please slow down.",
    "error_code": "RATE_LIMIT_EXCEEDED",
    "retry_after": 60
}
```

### Video Not Found
```json
{
    "detail": "Video not found or unavailable",
    "error_code": "VIDEO_NOT_FOUND"
}
```

### File Too Large
```json
{
    "detail": "File size exceeds maximum allowed (2GB)",
    "error_code": "FILE_TOO_LARGE"
}
```

## JavaScript/Fetch Examples

### Using Fetch API
```javascript
// Get video metadata
const response = await fetch('http://localhost:8000/api/metadata?url=' + encodeURIComponent(videoUrl));
const metadata = await response.json();
console.log(metadata.title);

// Start download
const downloadResponse = await fetch('http://localhost:8000/api/download', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        url: videoUrl,
        format: 'mp4',
        quality: '1080p'
    })
});
const { task_id } = await downloadResponse.json();

// Poll for status
const interval = setInterval(async () => {
    const status = await fetch(`http://localhost:8000/api/download/${task_id}`);
    const data = await status.json();
    
    if (data.status === 'completed') {
        clearInterval(interval);
        window.location.href = `http://localhost:8000/api/download/${task_id}/file`;
    }
}, 2000);
```

## Python Examples

### Using Requests
```python
import requests

BASE_URL = "http://localhost:8000/api"

# Get metadata
response = requests.get(f"{BASE_URL}/metadata", params={"url": video_url})
metadata = response.json()
print(f"Title: {metadata['title']}")

# Search YouTube
results = requests.get(f"{BASE_URL}/search", params={"q": "python tutorial", "limit": 5})
for video in results.json():
    print(f"- {video['title']}")

# Queue download
download = requests.post(f"{BASE_URL}/download", json={
    "url": video_url,
    "format": "mp4",
    "quality": "720p"
})
task_id = download.json()["task_id"]

# Check status
status = requests.get(f"{BASE_URL}/download/{task_id}")
print(status.json())
```
