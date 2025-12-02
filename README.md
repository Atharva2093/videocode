# 📹 YouTube Downloader (MP4 Only)

*A fast, clean and modern YouTube downloader — with real-time progress, folder selection, and full MP4 quality options.*

<p align="center">
  <img src="screenshot-ui.png" width="700"/>
</p>

---

## 🚀 Overview

This is a **browser-based YouTube video downloader** built with:

* ⚡ **FastAPI** backend (yt-dlp engine)
* 🎨 **Clean, minimal frontend** (vanilla HTML/CSS/JS)
* 📂 **Chrome/Edge folder picker support** (File System Access API)
* 📉 **Real-time streaming progress bar**
* 🎞 **All MP4 quality options** (360p → 1080p → 4K/8K if available)
* 🧹 No heavy animations / No clutter
* 🌐 Fully deployable to **Vercel (frontend)** + **Render (backend)**

MP3 support has been removed by design for stability and simplicity.

---

## ✨ Features

### **🎥 YouTube Video Fetching**

* Paste any YouTube link
* Extracts:

  * Title
  * Thumbnail
  * Duration
  * All available MP4 qualities

### **📂 Choose Download Location (Chrome/Edge)**

* Before each download, a modal appears:

  * “📂 Select Folder & Save”
  * If cancelled → download stops
  * Saves using **original sanitized video title**

### **📡 Real-Time Progress**

* Smart animated progress bar
* Percentage indicator
* Auto completes to 100% when file is saved

### **🔍 URL Auto-Detect**

Automatically picks YouTube links from clipboard when user clicks anywhere.

### **📁 Recent Download History**

* Stores last 5 downloads
* Shows filename + timestamp
* Saved locally via LocalStorage

### **🌓 Light/Dark Mode**

Toggle for clean, minimal UI themes.

### **⚠️ Clear & Clean Error Handling**

User sees friendly messages:

* Invalid YouTube URL
* Could not connect to server
* Video cannot be downloaded
* DRM-protected / login-required videos

---

## 🧱 Tech Stack

### **Frontend**

* Vanilla JavaScript
* HTML5 + CSS3
* File System Access API
* Minimalistic design (no frameworks)

### **Backend**

* Python 3
* FastAPI
* yt-dlp (latest version)
* FFmpeg (Render installed via render.yaml)
* Streaming downloads (no memory overload)

### **Deployment**

* Frontend → **Vercel**
* Backend → **Render Web Service**
* API auto-detected based on environment

---

## 🏗 Architecture

```
YouTube Link → Frontend → /api/metadata → yt-dlp parse → Qualities returned
User selects quality → Folder Picker → /api/download → Streaming → Saved to disk
```

### Backend flow

```
FastAPI → yt-dlp → FFmpeg → Stream chunks → Browser → File System Access API
```

---

## 🖼 Screenshots

Add your own screenshots here:

```
/screenshots/home.png
/screenshots/fetch.png
/screenshots/download-modal.png
/screenshots/progress.png
```

---

## 🔌 API Documentation

### 1. **GET /api/health**

```
{
  "status": "ok",
  "ffmpeg_available": true,
  "yt_dlp_version": "2025.01.01"
}
```

### 2. **GET /api/metadata?url=YOUTUBE_URL**

Returns:

```
{
  "title": "...",
  "thumbnail": "...",
  "duration": 123,
  "formats": [
    { "id": "18", "ext": "mp4", "quality": 360, "height": 360 },
    ...
  ]
}
```

### 3. **GET /api/download?url=...&format_id=...**

* Streams video chunks
* Sets `Content-Disposition: attachment; filename="<title>.mp4"`

---

## 🖥 Local Development

### 1. Clone repo

```
git clone https://github.com/YOUR_USERNAME/videocode
cd videocode
```

### 2. Backend

```
cd backend
pip install -r requirements.txt
uvicorn main:app --host 127.0.0.1 --port 8000
```

### 3. Frontend

```
cd frontend
python -m http.server 3000
```

Open:

```
http://127.0.0.1:3000
```

---

## 🌐 Deployment

### 🔧 Backend (Render)

Use **render.yaml**:

```yaml
services:
  - type: web
    name: yt-downloader-backend
    runtime: python
    buildCommand: |
      apt-get update && apt-get install -y ffmpeg
      pip install -r requirements.txt
    startCommand: uvicorn main:app --host 0.0.0.0 --port $PORT
```

Deploy → copy backend API URL → used by frontend.

---

### 🎨 Frontend (Vercel)

Project settings:

```
Framework: Other
Output directory: frontend
```

Add vercel.json:

```json
{
  "rewrites": [
    { "source": "/api/(.*)", "destination": "https://YOUR_RENDER_BACKEND_URL/api/$1" }
  ]
}
```

Deploy.

---

## ❗ Limitations

* DRM-protected videos **cannot** be downloaded
* Login-required videos not supported
* Folder picker only works on:

  * Chrome
  * Edge
  * Arc

Other browsers fall back to normal download dialog.

---

## 🔐 Security Notes

* Only YouTube URLs are allowed
* Rate limiting enabled
* No cookies or authentication used
* No video caching (for safety + bandwidth control)

---

## 📝 License

MIT License © 2025 Atharva

---

## ❤️ Credits

Built by Atharva
Powered by FastAPI + yt-dlp + FFmpeg
