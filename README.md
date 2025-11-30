# 🎬 YouTube Video Downloader

A full-stack YouTube video and playlist downloader with a modern PWA web interface and powerful FastAPI backend.

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com)
[![PWA](https://img.shields.io/badge/PWA-Ready-purple.svg)](https://web.dev/progressive-web-apps/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![CI/CD](https://github.com/Atharva2093/videocode/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/Atharva2093/videocode/actions)

<p align="center">
  <img src="screenshots/desktop.png" alt="Desktop Screenshot" width="700">
</p>

---

## ✨ Features

### 📱 Progressive Web App (PWA)
- **Installable** - Add to home screen on mobile/desktop
- **Offline Support** - Service worker caches UI shell
- **Auto-paste** - Detects YouTube URLs from clipboard
- **Mobile-first Design** - Optimized for touch devices
- **Dark Theme** - Easy on the eyes

### 🎯 Mobile Optimization (Phase 5)
- **Mobile Presets**:
  - Auto Best - Smart selection for your device
  - Mobile Video - 480p MP4 (~50MB/10min)
  - Small Audio - 64kbps MP3 (~5MB/10min)
- **QR Code Sharing** - Transfer files PC → Mobile instantly

### 🖥️ Web Interface
- Modern, responsive dark-themed UI
- Video metadata preview with thumbnail
- **Format tabs**: Video, Audio, Mobile-optimized
- Quality selection grid (2160p to 360p)
- Playlist support with selective downloads
- Real-time download progress tracking
- Download queue management
- Toast notifications

### 🔧 API Backend
- RESTful API built with FastAPI
- Async download with queue management
- Rate limiting & CORS protection
- Comprehensive error handling
- Server-side logging
- Health monitoring endpoint

### 🎨 Additional Apps
- **GUI Application** - Tkinter desktop interface
- **CLI Tool** - Command-line for automation

---

## 📸 Screenshots

<table>
  <tr>
    <td><img src="screenshots/mobile.png" alt="Mobile View" width="250"></td>
    <td><img src="screenshots/desktop.png" alt="Desktop View" width="450"></td>
  </tr>
  <tr>
    <td align="center">Mobile View</td>
    <td align="center">Desktop View</td>
  </tr>
</table>

---

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- FFmpeg (for audio extraction)
- Git

### Local Development

```bash
# Clone the repository
git clone https://github.com/Atharva2093/videocode.git
cd videocode

# Install backend dependencies
cd backend
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Start the backend server
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# In another terminal, serve the frontend
cd ../frontend
python -m http.server 3000
```

**Access:**
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
│   │   ├── download_manager.py # Download queue manager
│   │   └── ytdlp_downloader.py # yt-dlp wrapper
│   ├── tests/                  # Unit tests
│   ├── main.py                 # FastAPI application
│   ├── config.py               # Configuration
│   ├── models.py               # Pydantic models
│   ├── errors.py               # Error handling
│   ├── requirements.txt        # Python dependencies
│   └── Dockerfile              # Docker configuration
│
├── frontend/                   # PWA Frontend
│   ├── css/
│   │   └── styles.css          # Mobile-first CSS
│   ├── js/
│   │   ├── api.js              # API client
│   │   └── app.js              # Main application
│   ├── icons/                  # PWA icons
│   ├── index.html              # Main page
│   ├── manifest.json           # PWA manifest
│   └── sw.js                   # Service worker
│
├── .github/
│   └── workflows/
│       └── ci-cd.yml           # CI/CD pipeline
│
├── youtube_downloader_gui.py   # Standalone GUI app
├── youtube_downloader_yt_dlp.py # CLI tool
│
├── docker-compose.yml          # Docker Compose config
├── render.yaml                 # Render deployment
├── netlify.toml                # Netlify deployment
├── vercel.json                 # Vercel deployment
└── README.md                   # This file
```

---

## 🔌 API Documentation

### Endpoints Overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check with yt-dlp version |
| GET | `/api/metadata?url=` | Get video metadata |
| GET | `/api/playlist?url=` | Get playlist info |
| GET | `/api/thumbnail?url=` | Get thumbnail image |
| POST | `/api/download` | Queue async download |
| POST | `/api/download/direct` | Direct download (streaming) |
| GET | `/api/download/{task_id}` | Get download status |
| GET | `/api/download/{task_id}/file` | Get completed file |
| POST | `/api/convert` | Convert to format |
| POST | `/api/mobile-compression` | Mobile-optimized download |
| GET | `/api/queue` | Get queue status |
| DELETE | `/api/queue/clear` | Clear completed |

### Example API Calls

```bash
# Get video metadata
curl "http://localhost:8000/api/metadata?url=https://youtube.com/watch?v=VIDEO_ID"

# Start download
curl -X POST "http://localhost:8000/api/download" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://youtube.com/watch?v=VIDEO_ID","quality":"720p","format":"mp4"}'

# Mobile-optimized download
curl -X POST "http://localhost:8000/api/mobile-compression" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://youtube.com/watch?v=VIDEO_ID","max_resolution":"480p"}'
```

### Error Response Format

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid YouTube URL",
    "status": 400,
    "timestamp": "2024-01-15T10:30:00Z",
    "details": {
      "field": "url"
    }
  }
}
```

---

## 🚀 Deployment

### Option 1: Render (Backend)

1. Connect your GitHub repo to [Render](https://render.com)
2. Create a new Web Service
3. Select Python environment
4. Set build command: `pip install -r backend/requirements.txt`
5. Set start command: `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`

Or use the included `render.yaml` for Blueprint deployment.

### Option 2: Netlify (Frontend)

1. Connect your GitHub repo to [Netlify](https://netlify.com)
2. Set publish directory: `frontend`
3. Set build command: `echo 'Static site ready'`
4. Configure API redirect in `netlify.toml`

### Option 3: Vercel (Frontend)

1. Connect your GitHub repo to [Vercel](https://vercel.com)
2. Import project
3. Configuration is in `vercel.json`

### Option 4: Docker

```bash
# Build and run with Docker Compose
docker-compose up -d

# Or build manually
docker build -t youtube-downloader-api -f backend/Dockerfile .
docker run -p 8000:8000 youtube-downloader-api
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `0.0.0.0` | Server host |
| `PORT` | `8000` | Server port |
| `DEBUG` | `true` | Debug mode |
| `DOWNLOAD_DIR` | `./downloads` | Download directory |
| `MAX_CONCURRENT_DOWNLOADS` | `3` | Max parallel downloads |
| `MAX_FILE_SIZE_MB` | `500` | Max file size limit |
| `MAX_VIDEO_DURATION` | `7200` | Max video duration (seconds) |
| `CORS_ORIGINS` | `*` | Allowed CORS origins |

---

## 🧪 Testing

```bash
# Run backend tests
cd backend
pip install pytest pytest-asyncio pytest-cov
pytest tests/ -v --cov=.

# Run linting
flake8 backend --max-line-length=120
black --check backend
```

---

## 🤝 Contributing

Contributions are welcome! Here's how to get started:

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. **Make your changes**
4. **Run tests**
   ```bash
   pytest tests/ -v
   ```
5. **Commit your changes**
   ```bash
   git commit -m 'Add amazing feature'
   ```
6. **Push to your branch**
   ```bash
   git push origin feature/amazing-feature
   ```
7. **Open a Pull Request**

### Development Guidelines

- Follow PEP 8 for Python code
- Use meaningful commit messages
- Add tests for new features
- Update documentation as needed

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - YouTube downloading library
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [QRCode.js](https://davidshimjs.github.io/qrcodejs/) - QR code generation

---

## ⚠️ Disclaimer

This tool is for educational purposes only. Please respect YouTube's Terms of Service and copyright laws. Only download content you have permission to download.

---

## 📊 Roadmap

- [x] Phase 1: Core backend with FastAPI
- [x] Phase 2: Enhanced API endpoints
- [x] Phase 3: Mobile-first responsive UI
- [x] Phase 4: PWA support
- [x] Phase 5: Mobile optimization & QR sharing
- [x] Phase 6: Error handling & deployment
- [ ] Phase 7: User accounts & history
- [ ] Phase 8: Browser extension
