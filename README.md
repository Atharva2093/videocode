# 🎬 YouTube Video Downloader

A full-stack YouTube video and playlist downloader with a modern web interface and powerful API backend.

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## ✨ Features

### 🖥️ Web Interface (NEW!)
- Modern, responsive dark-themed UI
- Video metadata preview with thumbnail
- Playlist support with selective downloads
- Real-time download progress tracking
- Download queue management
- Multiple format and quality options

### 🔧 API Backend (NEW!)
- RESTful API built with FastAPI
- Concurrent download support (configurable workers)
- Download queue with task management
- Video/playlist info extraction
- Multiple format support (MP4, WebM, MP3)
- Health monitoring endpoint

### 🖱️ GUI Application
- Easy-to-use Tkinter interface
- Download queue for multiple videos
- Video preview with thumbnail
- Playlist support with checkboxes
- Select video format (mp4/webm) or audio-only (mp3)
- Choose quality: best, medium, worst
- Progress bar and status updates
- Cancel button for active downloads

### ⌨️ Command-Line Interface
- Interactive mode for multiple downloads
- Playlist support with `--playlist all` or `--playlist select`
- Preview mode with `--preview` flag
- Pass arguments for URL, output folder, format, quality
- Debug mode for troubleshooting

---

## 🚀 Quick Start

### Prerequisites

- Python 3.9 or higher
- FFmpeg (for audio extraction)
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Atharva2093/videocode.git
   cd videocode
   ```

2. **Install backend dependencies**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. **Copy environment file**
   ```bash
   cp .env.example .env
   ```

4. **Start the backend server**
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

5. **Open the frontend**
   - Open `frontend/index.html` in your browser, or
   - Serve it with a local server:
     ```bash
     cd frontend
     python -m http.server 3000
     ```

6. **Access the application**
   - Frontend: http://localhost:3000
   - API Docs: http://localhost:8000/api/docs

### Docker Deployment

```bash
docker-compose up -d
```

---

## 📁 Project Structure

```
videocode/
├── backend/                    # FastAPI Backend
│   ├── routes/                 # API endpoints
│   │   ├── download.py         # Download endpoints
│   │   ├── video_info.py       # Video info endpoints
│   │   └── health.py           # Health check
│   ├── worker/                 # Background workers
│   │   └── download_manager.py # Download queue manager
│   ├── main.py                 # FastAPI application
│   ├── config.py               # Configuration
│   ├── models.py               # Pydantic models
│   ├── requirements.txt        # Python dependencies
│   └── Dockerfile              # Docker configuration
│
├── frontend/                   # Web Frontend
│   ├── css/
│   │   └── styles.css          # Styling
│   ├── js/
│   │   ├── api.js              # API client
│   │   └── app.js              # Main application
│   └── index.html              # Main page
│
├── shared/                     # Shared utilities
│   └── utils.py                # Common functions
│
├── youtube_downloader_gui.py   # Standalone GUI app
├── youtube_downloader_yt_dlp.py # CLI tool (yt-dlp)
├── youtube_downloader.py       # CLI tool (pytube)
│
├── docker-compose.yml          # Docker Compose config
├── nginx.conf                  # Nginx configuration
├── .env.example                # Environment template
├── .gitignore                  # Git ignore rules
└── README.md                   # This file
```

---

## 🔌 API Endpoints

### Phase 1 - Core Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| POST | `/api/info` | Get video/playlist info (legacy) |

### Phase 2 - Enhanced Endpoints

#### 📊 Metadata & Info
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/metadata?url=` | Get comprehensive video metadata with formats & sizes |
| GET | `/api/playlist?url=` | Get playlist with all video titles & IDs |
| GET | `/api/thumbnail?url=&quality=` | Get video thumbnail as image (sd/mq/hq/maxres) |
| GET | `/api/formats/{video_id}` | Get available formats for a video |

#### ⬇️ Download
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/download` | Queue-based async download |
| POST | `/api/download/direct` | Direct download (returns file immediately) |
| GET | `/api/download/{task_id}` | Get download status |
| GET | `/api/download/{task_id}/file` | Download completed file |
| POST | `/api/download/cancel` | Cancel a download |
| DELETE | `/api/download/{task_id}` | Remove download from history |

#### 🔄 Convert & Compress
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/convert` | Download & convert to format (mp3/mp4/webm) |
| POST | `/api/mobile-compression` | Mobile-optimized download (480p/64kbps) |

#### 📋 Queue Management
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/queue` | Get queue status |
| DELETE | `/api/queue/clear` | Clear completed downloads |

### Example API Calls

```bash
# Get video metadata
curl "http://localhost:8000/api/metadata?url=https://youtube.com/watch?v=VIDEO_ID"

# Get playlist info
curl "http://localhost:8000/api/playlist?url=https://youtube.com/playlist?list=PLAYLIST_ID"

# Get thumbnail
curl "http://localhost:8000/api/thumbnail?url=https://youtube.com/watch?v=VIDEO_ID&quality=hq"

# Direct download
curl -X POST "http://localhost:8000/api/download/direct" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://youtube.com/watch?v=VIDEO_ID","quality":"720p","format":"mp4"}' \
  -o video.mp4

# Convert to MP3
curl -X POST "http://localhost:8000/api/convert" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://youtube.com/watch?v=VIDEO_ID","output_format":"mp3","audio_quality":"high"}' \
  -o audio.mp3

# Mobile compression
curl -X POST "http://localhost:8000/api/mobile-compression" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://youtube.com/watch?v=VIDEO_ID","max_resolution":"480p"}' \
  -o mobile_video.mp4
```

---

## ⚙️ Configuration

Environment variables (`.env`):

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `0.0.0.0` | Server host |
| `PORT` | `8000` | Server port |
| `DEBUG` | `true` | Debug mode |
| `DOWNLOAD_DIR` | `./downloads` | Download directory |
| `MAX_CONCURRENT_DOWNLOADS` | `3` | Max parallel downloads |
| `MAX_QUEUE_SIZE` | `50` | Max queue size |

---

## 🎯 Usage

### Web Interface
1. Open the frontend in your browser
2. Paste a YouTube URL
3. Click "Preview" to see video info
4. Select format and quality
5. Click "Download"
6. Monitor progress in the queue

### CLI Tool
```bash
# Download a video
python youtube_downloader_yt_dlp.py "https://youtube.com/watch?v=VIDEO_ID"
```

### GUI App
```bash
python youtube_downloader_gui.py
```

---

## 📝 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - YouTube downloading library
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [pytube](https://github.com/pytube/pytube) - Alternative YouTube library

## ⚠️ Disclaimer

This tool is for educational purposes only. Please respect YouTube's Terms of Service and copyright laws.
