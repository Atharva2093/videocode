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
- **Dark/Light Theme** - Toggle with one click

### 🔍 YouTube Search (No API Key!)
- Search YouTube directly from the app
- Uses yt-dlp's ytsearch feature
- Results cached for 1 hour
- Click to download any result

### 🎯 Mobile Optimization
- **Mobile Presets**:
  - Auto Best - Smart selection for your device
  - Mobile Video - 480p MP4 (~50MB/10min)
  - Small Audio - 64kbps MP3 (~5MB/10min)
- **QR Code Sharing** - Transfer files PC → Mobile instantly

### 📝 Subtitle Support
- View available subtitle languages
- Download subtitles separately
- Embed subtitles into video

### 🖥️ Web Interface
- Modern, responsive dark/light themed UI
- Video metadata preview with thumbnail
- **Format tabs**: Video, Audio, Mobile-optimized
- Quality selection grid (2160p to 360p)
- Playlist support with selective downloads
- Real-time download progress tracking
- Download queue management
- Toast notifications
- Settings modal with preferences

### 🔧 API Backend
- RESTful API built with FastAPI
- Async download with queue management
- Metadata caching (1-hour TTL)
- Rate limiting (30 req/min, 3 downloads/min)
- CORS protection
- Comprehensive error handling
- Server-side logging with rotation
- Health monitoring endpoint

### 🧪 Testing
- Backend integration tests (pytest)
- Frontend E2E tests (Playwright)
- Lighthouse CI for performance

### 🎨 Additional Apps
- **GUI Application** - Tkinter desktop interface
- **CLI Tool** - Command-line for automation

---

## 📚 Documentation

- [📐 Architecture](docs/ARCHITECTURE.md) - System design and component diagram
- [⚠️ Known Issues](docs/KNOWN_ISSUES.md) - Limitations and workarounds
- [📖 API Examples](docs/API_EXAMPLES.md) - cURL, JavaScript, Python examples

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

---

## 🔐 Authentication (Required)

YouTube now requires authentication to prevent bot detection. You **must** export cookies from your browser.

### Why is this needed?

YouTube shows "Sign in to confirm you're not a bot" errors when downloading videos without authentication. By using cookies from a logged-in browser session, yt-dlp can bypass this restriction.

### Export Cookies

**Option 1: Use the built-in utility (Recommended)**

```bash
cd backend/tools
python export_cookies.py chrome    # or edge, firefox, brave
```

**Option 2: Manual export with yt-dlp**

```bash
yt-dlp --cookies-from-browser chrome --cookies backend/cookies.txt https://www.youtube.com
```

### Steps:

1. **Log into YouTube** in your browser (Chrome, Edge, Firefox, or Brave)
2. **Close the browser** (required for cookie access)
3. **Run the export script**:
   ```bash
   python backend/tools/export_cookies.py
   ```
4. **Restart the backend** - it will load the cookies automatically

### Verify cookies are loaded:

```bash
curl http://127.0.0.1:8000/api/health
# Should return: {"status":"ok","cookies_loaded":true}
```

### Reload cookies via API:

```bash
curl "http://127.0.0.1:8000/api/reload-cookies?browser=chrome"
```

### For Render/Production:

1. Export cookies locally using the script
2. Create a **Secret File** in Render dashboard
3. Name it `cookies.txt` and paste the contents
4. Mount path: `/etc/secrets/cookies.txt`

⚠️ **Note**: Cookies expire! Re-export every 1-2 weeks or when you see bot detection errors.

---

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
│   │   ├── search.py           # YouTube search & subtitles
│   │   └── health.py           # Health check
│   ├── worker/                 # Background workers
│   │   ├── download_manager.py # Download queue manager
│   │   └── ytdlp_downloader.py # yt-dlp wrapper
│   ├── tests/                  # Backend tests
│   │   └── test_integration.py # Integration tests
│   ├── main.py                 # FastAPI application
│   ├── config.py               # Configuration
│   ├── models.py               # Pydantic models
│   ├── errors.py               # Error handling
│   ├── requirements.txt        # Python dependencies
│   └── Dockerfile              # Docker configuration
│
├── frontend/                   # PWA Frontend
│   ├── css/
│   │   └── styles.css          # Mobile-first CSS (dark/light)
│   ├── js/
│   │   ├── api.js              # API client
│   │   └── app.js              # Main application
│   ├── tests/                  # Frontend tests
│   │   └── e2e.spec.js         # Playwright E2E tests
│   ├── icons/                  # PWA icons
│   ├── index.html              # Main page
│   ├── manifest.json           # PWA manifest
│   └── sw.js                   # Service worker
│
├── docs/                       # Documentation
│   ├── ARCHITECTURE.md         # System architecture
│   ├── KNOWN_ISSUES.md         # Known issues & workarounds
│   └── API_EXAMPLES.md         # API usage examples
│
├── .github/
│   └── workflows/
│       └── ci-cd.yml           # CI/CD pipeline
│
├── youtube_downloader_gui.py   # Standalone GUI app
├── youtube_downloader_yt_dlp.py # CLI tool
│
├── docker-compose.yml          # Docker Compose config
├── playwright.config.js        # Playwright test config
├── lighthouserc.json           # Lighthouse CI config
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
| GET | `/api/search?q=&limit=` | Search YouTube videos |
| GET | `/api/subtitles?url=&lang=` | Download subtitles |
| GET | `/api/subtitles/available?url=` | List available subtitles |

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

### Backend Tests

```bash
# Install test dependencies
cd backend
pip install pytest pytest-asyncio pytest-cov httpx

# Run integration tests
pytest tests/ -v --cov=.

# Run with coverage report
pytest tests/ -v --cov=. --cov-report=html
```

### Frontend E2E Tests

```bash
# Install Playwright
npm install @playwright/test
npx playwright install

# Run E2E tests
npx playwright test

# Run with UI
npx playwright test --ui
```

### Lighthouse CI

```bash
# Install Lighthouse CI
npm install -g @lhci/cli

# Run audit
lhci autorun
```

### Linting

```bash
# Backend
flake8 backend --max-line-length=120
black --check backend

# Frontend
npx eslint frontend/js
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
- [x] Phase 7: Frontend polish (theme toggle, settings, progress UI)
- [x] Phase 8: Backend enhancements (search, subtitles, rate limiting)
- [x] Phase 9: PWA finalization (service worker caching)
- [x] Phase 10: Advanced features (YouTube search)
- [x] Phase 11: Testing (Playwright, Lighthouse CI, integration tests)
- [x] Phase 12: Documentation (architecture, API examples)
- [ ] Phase 13: User accounts & history
- [ ] Phase 14: Browser extension
