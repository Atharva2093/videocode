# YouTube Video Downloader - Ultra-Fast CLI

**Simple • Fast • Local-Only**

Download YouTube videos at **maximum speed** using this lightweight command-line tool. Runs entirely on your computer with no web browser or server required.

## ✨ Features

- ⚡ **Ultra-Fast Downloads** - Uses aria2c for 5-15x speed boost (16 parallel connections)
- 📁 **Custom Save Location** - Choose where to save your videos
- 🎯 **MP4 Format** - Downloads clean, compatible MP4 files
- 🏠 **100% Local** - Runs offline, no cloud, no tracking
- 🎨 **Simple CLI** - Easy interactive prompts
- 🚀 **Optimized** - Automatic speed optimization with fallback modes

## 📋 Requirements

**Required:**
- Python 3.8 or newer
- Internet connection (for downloading)

**Optional (for maximum speed):**
- aria2c - Enables 5-15x faster downloads

## 🚀 Quick Start

### 1. Install Python

Download and install Python 3.8+ from [python.org](https://www.python.org/downloads/)

**Important:** During installation, check "Add Python to PATH"

Verify installation:
```bash
python --version
```

### 2. Clone or Download This Project

```bash
git clone https://github.com/yourusername/videocode.git
cd videocode
```

Or download as ZIP and extract.

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

This installs yt-dlp (the YouTube download engine).

### 4. Run the Downloader

```bash
python downloader.py
```

## 💨 Enable Maximum Speed (Highly Recommended)

Install **aria2c** for 5-15x faster downloads:

### Windows

1. Download from [GitHub Releases](https://github.com/aria2/aria2/releases)
2. Extract `aria2c.exe`
3. Add to PATH or place in `C:\Windows\System32`

### Linux

```bash
sudo apt update
sudo apt install aria2
```

### macOS

```bash
brew install aria2
```

### Verify Installation

```bash
aria2c --version
```

## 📖 Usage Example

```
======================================================================
  YOUTUBE VIDEO DOWNLOADER - Ultra-Fast CLI
======================================================================
  [SPEED MODE] aria2c detected - Maximum speed enabled!
======================================================================

Enter YouTube URL:
> https://youtube.com/watch?v=dQw4w9WgXcQ

[FETCHING] Getting video information...

[VIDEO TITLE] Rick Astley - Never Gonna Give You Up
[DURATION] 3m 33s

Available MP4 qualities:
----------------------------------------------------------------------
  1) 1080p [with audio]   (ID: 22    ) - 45.2 MB
  2) 720p  [with audio]   (ID: 136   ) - 28.5 MB
  3) 480p  [video only]   (ID: 135   ) - 15.3 MB
  4) Best quality available
----------------------------------------------------------------------

Choose quality number: 2
[SELECTED] 720p

Enter download folder path:
(Leave empty to use current directory)
> C:\Users\YourName\Videos

[USING] Download folder: C:\Users\YourName\Videos

======================================================================
  STARTING DOWNLOAD
======================================================================

[SPEED BOOST] Using aria2c (16 parallel connections)

[DOWNLOADING] Rick Astley - Never Gonna Give You Up
[SAVING TO] C:\Users\YourName\Videos

Progress:  100.00% | Speed:  12.34 MB/s | ETA:   0s
[PROCESSING] Finalizing download...

======================================================================
  DOWNLOAD COMPLETE!
======================================================================

[SUCCESS] Video saved to:
  C:\Users\YourName\Videos\Rick Astley - Never Gonna Give You Up.mp4

[FILE SIZE] 28.50 MB

======================================================================
```

## 🎯 Supported URLs

- Standard: `https://youtube.com/watch?v=VIDEO_ID`
- Short: `https://youtu.be/VIDEO_ID`
- Shorts: `https://youtube.com/shorts/VIDEO_ID`
- Embed: `https://youtube.com/embed/VIDEO_ID`

## 🔧 Troubleshooting

### Slow Downloads (1-3 MB/s)?

**Solution:** Install aria2c (see [Enable Maximum Speed](#-enable-maximum-speed-highly-recommended))

**Speed comparison:**
- Without aria2c: 1-3 MB/s (single connection)
- With aria2c: 10-20+ MB/s (16 parallel connections)

### "No MP4 formats available"

**Cause:** Video doesn't have MP4 format

**Solution:** Try a different video

### "Video is unavailable or removed"

**Causes:**
- Video was deleted by creator
- Video is region-locked
- Video is age-restricted
- Video is private

**Solution:** Try a different public video

### "Video is DRM-protected"

**Cause:** Video has digital rights management (premium content)

**Solution:** This downloader only works with free, public YouTube videos

### "Invalid download folder"

**Cause:** Folder path doesn't exist or no write permission

**Solution:**
- Use full absolute path (e.g., `C:\Users\Name\Videos`)
- Or leave empty to use current directory
- Make sure folder is writable

### "Network timeout - connection too slow"

**Causes:**
- Slow internet connection
- Network congestion
- ISP throttling

**Solutions:**
1. Install aria2c for better reliability
2. Try again later
3. Use wired connection instead of Wi-Fi
4. Choose lower quality (720p or 480p)

### Python not found

**Cause:** Python not installed or not in PATH

**Solution:**
1. Reinstall Python from [python.org](https://www.python.org/downloads/)
2. During installation, check "Add Python to PATH"
3. Restart terminal/command prompt

## 📊 Performance Tips

### Maximum Speed Configuration

1. ✅ **Install aria2c** (5-15x speed boost)
2. ✅ **Use wired Ethernet** (faster than Wi-Fi)
3. ✅ **Choose 720p** (good balance of quality and speed)
4. ✅ **Close other downloads** (free up bandwidth)
5. ✅ **Download during off-peak hours**

### Quality vs Speed

| Quality | File Size (10min) | Download Time (with aria2c) |
|---------|-------------------|------------------------------|
| 1080p   | ~200 MB           | ~15 seconds                  |
| 720p    | ~100 MB           | ~8 seconds                   |
| 480p    | ~50 MB            | ~4 seconds                   |

*Times are approximate with 100 Mbps connection

## 📁 Project Structure

```
videocode/
├── downloader.py          # Main script (run this)
├── simple_downloader.py   # Core download functions
├── exceptions.py          # Error handling
├── requirements.txt       # Dependencies (yt-dlp)
├── README.md             # This file
└── HOW_TO_USE.md         # Detailed guide
```

## ❓ FAQ

**Q: Is this legal?**  
A: Use only for personal purposes and videos you have permission to download. Respect copyright and YouTube's Terms of Service.

**Q: Does it work offline?**  
A: You need internet to download videos, but the tool runs locally on your machine.

**Q: Can I download playlists?**  
A: Not currently. Download videos one at a time.

**Q: Does it save my data or track me?**  
A: No. Everything runs 100% locally. No analytics, no tracking, no cloud storage.

**Q: Why do I need aria2c?**  
A: aria2c enables parallel downloading (16 connections), making downloads 5-15x faster. It's optional but highly recommended.

**Q: Can I download 4K videos?**  
A: Yes, if the video has 4K MP4 format available, you'll see it in the quality list.

**Q: Where are videos saved?**  
A: You choose the folder each time. If you leave it empty, videos save to the current directory.

**Q: Can I cancel a download?**  
A: Yes, press `Ctrl+C` (or `Cmd+C` on Mac) to cancel.

## 🆘 Getting Help

For detailed instructions, see [HOW_TO_USE.md](HOW_TO_USE.md)

For issues:
1. Check the [Troubleshooting section](#-troubleshooting)
2. Make sure yt-dlp is updated: `pip install --upgrade yt-dlp`
3. Check your internet connection
4. Try a different video

## 🔄 Updates

Keep yt-dlp updated (YouTube changes frequently):

```bash
pip install --upgrade yt-dlp
```

## 📜 License

MIT License - Free for personal use

---

**Made with ❤️ for fast, simple, local video downloads**

**No web browser • No server • No complexity • Just speed**
