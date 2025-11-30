# YouTube Downloader - Architecture Documentation

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           CLIENT LAYER                                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐               │
│  │   Browser    │    │  PWA (iOS/   │    │   Desktop    │               │
│  │   (Chrome,   │    │   Android)   │    │   App        │               │
│  │   Firefox)   │    │              │    │              │               │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘               │
│         │                   │                   │                        │
│         └───────────────────┼───────────────────┘                        │
│                             │                                            │
│                     ┌───────▼───────┐                                    │
│                     │  Service      │                                    │
│                     │  Worker       │                                    │
│                     │  (sw.js)      │                                    │
│                     └───────┬───────┘                                    │
│                             │                                            │
└─────────────────────────────┼────────────────────────────────────────────┘
                              │ HTTPS
                              │
┌─────────────────────────────┼────────────────────────────────────────────┐
│                           API LAYER                                      │
├─────────────────────────────┼────────────────────────────────────────────┤
│                             │                                            │
│         ┌───────────────────▼───────────────────┐                        │
│         │              FastAPI                   │                        │
│         │         (backend/main.py)              │                        │
│         │                                        │                        │
│         │  ┌──────────────────────────────────┐ │                        │
│         │  │        Middleware Layer          │ │                        │
│         │  │  • CORS                          │ │                        │
│         │  │  • Rate Limiting                 │ │                        │
│         │  │  • Error Handling                │ │                        │
│         │  └──────────────────────────────────┘ │                        │
│         │                                        │                        │
│         │  ┌────────────────────────────────────┐│                        │
│         │  │            Routes                  ││                        │
│         │  │  • /health      - Health check     ││                        │
│         │  │  • /metadata    - Video info       ││                        │
│         │  │  • /download    - Queue download   ││                        │
│         │  │  • /search      - YouTube search   ││                        │
│         │  │  • /subtitles   - Subtitles        ││                        │
│         │  │  • /playlist    - Playlist info    ││                        │
│         │  └────────────────────────────────────┘│                        │
│         └────────────────────────────────────────┘                        │
│                              │                                            │
└──────────────────────────────┼───────────────────────────────────────────┘
                               │
┌──────────────────────────────┼───────────────────────────────────────────┐
│                        SERVICE LAYER                                     │
├──────────────────────────────┼───────────────────────────────────────────┤
│                              │                                            │
│    ┌─────────────────────────▼─────────────────────────┐                  │
│    │              Download Manager                      │                  │
│    │         (worker/download_manager.py)               │                  │
│    │                                                    │                  │
│    │  • Async Queue Management                          │                  │
│    │  • Concurrent Download Control                     │                  │
│    │  • Progress Tracking                               │                  │
│    │  • Task State Management                           │                  │
│    └────────────────────────┬───────────────────────────┘                  │
│                             │                                              │
│    ┌────────────────────────▼───────────────────────────┐                  │
│    │              yt-dlp Downloader                      │                  │
│    │         (worker/ytdlp_downloader.py)                │                  │
│    │                                                     │                  │
│    │  • Video Metadata Extraction                        │                  │
│    │  • Format Selection                                 │                  │
│    │  • Download Execution                               │                  │
│    │  • Temp File Cleanup                                │                  │
│    └────────────────────────┬────────────────────────────┘                  │
│                             │                                              │
└─────────────────────────────┼──────────────────────────────────────────────┘
                              │
┌─────────────────────────────┼──────────────────────────────────────────────┐
│                       EXTERNAL SERVICES                                     │
├─────────────────────────────┼──────────────────────────────────────────────┤
│                             │                                               │
│  ┌──────────────────────────▼─────────────────────────┐                     │
│  │                    yt-dlp                           │                     │
│  │           (YouTube-DL Python Library)               │                     │
│  │                                                     │                     │
│  │  • Video/Audio Extraction                           │                     │
│  │  • Format Conversion                                │                     │
│  │  • Playlist Processing                              │                     │
│  │  • Subtitle Download                                │                     │
│  └────────────────────────────┬────────────────────────┘                     │
│                               │                                              │
│  ┌────────────────────────────▼────────────────────────┐                     │
│  │                   FFmpeg                             │                     │
│  │            (Media Processing)                        │                     │
│  │                                                      │                     │
│  │  • Video/Audio Encoding                              │                     │
│  │  • Format Conversion                                 │                     │
│  │  • Mobile Compression                                │                     │
│  │  • Subtitle Embedding                                │                     │
│  └─────────────────────────────────────────────────────┘                     │
│                                                                              │
│  ┌─────────────────────────────────────────────────────┐                     │
│  │                 YouTube Servers                      │                     │
│  │                                                      │                     │
│  │  • Video/Audio Streams                               │                     │
│  │  • Metadata API                                      │                     │
│  │  • Thumbnail Images                                  │                     │
│  │  • Subtitle Tracks                                   │                     │
│  └─────────────────────────────────────────────────────┘                     │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

## Data Flow

### 1. Video Metadata Request
```
User → Frontend → /api/metadata → yt-dlp → YouTube → Response
                                     ↓
                              Metadata Cache (1hr TTL)
```

### 2. Download Request
```
User → Frontend → /api/download → Download Queue
                                      ↓
                               Download Manager
                                      ↓
                               yt-dlp + FFmpeg
                                      ↓
                               Temp Storage
                                      ↓
                               Download File
```

### 3. YouTube Search
```
User → Frontend → /api/search → yt-dlp (ytsearch)
                                     ↓
                              Search Cache
                                     ↓
                               Response
```

## Component Details

### Frontend Components
| Component | File | Purpose |
|-----------|------|---------|
| App | `js/app.js` | Main application logic |
| API Client | `js/api.js` | API communication |
| Service Worker | `sw.js` | Offline caching, PWA |
| Styles | `css/styles.css` | Mobile-first CSS |

### Backend Components
| Component | File | Purpose |
|-----------|------|---------|
| Main App | `main.py` | FastAPI application |
| Health Routes | `routes/health.py` | Health check endpoints |
| Video Info | `routes/video_info.py` | Metadata endpoints |
| Download | `routes/download.py` | Download endpoints |
| Search | `routes/search.py` | Search & subtitles |
| Errors | `errors.py` | Exception handling |
| Config | `config.py` | Settings management |

### Worker Components
| Component | File | Purpose |
|-----------|------|---------|
| Download Manager | `worker/download_manager.py` | Queue management |
| Downloader | `worker/ytdlp_downloader.py` | yt-dlp wrapper |

## API Endpoints Summary

### Health
- `GET /api/health` - Health check
- `GET /api/ping` - Ping/pong

### Video Information
- `GET /api/metadata` - Video metadata
- `GET /api/playlist` - Playlist info
- `GET /api/thumbnail` - Thumbnail URL

### Download
- `POST /api/download` - Queue download
- `GET /api/download/{task_id}` - Status
- `GET /api/download/{task_id}/file` - Download file
- `DELETE /api/download/{task_id}` - Remove task
- `POST /api/download/cancel` - Cancel download

### Search & Subtitles
- `GET /api/search` - YouTube search
- `GET /api/subtitles` - Available subtitles
- `POST /api/subtitles/download` - Download with subtitles

### Cache
- `GET /api/cache/stats` - Cache statistics
- `DELETE /api/cache/clear` - Clear cache

## Security Considerations

1. **Rate Limiting**: 30 requests/minute, 3 downloads/minute per IP
2. **CORS**: Restricted to configured origins
3. **Input Validation**: Pydantic models for all inputs
4. **File Size Limits**: 2GB max file size
5. **Duration Limits**: 2-hour max video duration

## Deployment Options

1. **Render** (`render.yaml`)
2. **Vercel** (`vercel.json`)
3. **Netlify** (`netlify.toml`)
4. **Docker** (`docker-compose.yml`)
5. **Cloudflare Pages** (static frontend)
