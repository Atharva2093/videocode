# How to Use - YouTube Video Downloader

Complete step-by-step guide for downloading YouTube videos at maximum speed.

## Table of Contents

1. [Installation Guide](#installation-guide)
2. [Basic Usage](#basic-usage)
3. [Advanced Usage](#advanced-usage)
4. [Speed Optimization](#speed-optimization)
5. [Troubleshooting](#troubleshooting)
6. [FAQ](#faq)
7. [Tips & Tricks](#tips--tricks)

---

## Installation Guide

### Step 1: Install Python

#### Windows
1. Go to [python.org/downloads](https://www.python.org/downloads/)
2. Download Python 3.8 or newer
3. Run installer
4. **✅ IMPORTANT:** Check "Add Python to PATH"
5. Click "Install Now"

Verify installation:
```cmd
python --version
```

#### Linux
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip

# Verify
python3 --version
```

#### macOS
```bash
# Install Homebrew first (if not installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python
brew install python3

# Verify
python3 --version
```

### Step 2: Get the Downloader

#### Option A: Clone with Git
```bash
git clone https://github.com/yourusername/videocode.git
cd videocode
```

#### Option B: Download ZIP
1. Go to GitHub repository
2. Click "Code" → "Download ZIP"
3. Extract the ZIP file
4. Open terminal/command prompt in the extracted folder

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

This installs `yt-dlp`, the YouTube download library.

### Step 4: Install aria2c (Optional but Recommended)

aria2c makes downloads **5-15x faster**!

#### Windows
1. Download from [github.com/aria2/aria2/releases](https://github.com/aria2/aria2/releases)
2. Download `aria2-x.xx.x-win-64bit-build1.zip`
3. Extract the ZIP file
4. Copy `aria2c.exe` to `C:\Windows\System32`

Or add to PATH:
- Right-click "This PC" → Properties
- Advanced system settings → Environment Variables
- Edit "Path" → Add aria2 folder path

Verify:
```cmd
aria2c --version
```

#### Linux
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install aria2

# Fedora
sudo dnf install aria2

# Arch
sudo pacman -S aria2

# Verify
aria2c --version
```

#### macOS
```bash
brew install aria2

# Verify
aria2c --version
```

---

## Basic Usage

### Running the Downloader

Open terminal/command prompt in the project folder:

```bash
python downloader.py
```

### Step-by-Step Walkthrough

#### Step 1: Enter URL

```
Enter YouTube URL:
> 
```

Paste any valid YouTube URL:
- `https://youtube.com/watch?v=VIDEO_ID`
- `https://youtu.be/VIDEO_ID`
- `https://youtube.com/shorts/VIDEO_ID`

Press Enter.

#### Step 2: View Video Info

The downloader fetches video information:

```
[FETCHING] Getting video information...

[VIDEO TITLE] Your Video Title Here
[DURATION] 5m 23s

Available MP4 qualities:
----------------------------------------------------------------------
  1) 1080p [with audio]   (ID: 22    ) - 120.5 MB
  2) 720p  [with audio]   (ID: 136   ) - 65.2 MB
  3) 480p  [video only]   (ID: 135   ) - 35.8 MB
  4) Best quality available
----------------------------------------------------------------------
```

**Understanding the format list:**
- **Quality** (1080p, 720p, etc.) - Video resolution
- **[with audio]** - Video has audio included
- **[video only]** - No audio (rare, usually has audio)
- **ID** - Internal format identifier
- **File size** - Estimated download size

#### Step 3: Choose Quality

```
Choose quality number: 
```

Enter a number (1-4):
- **1-3:** Specific quality
- **4:** Automatically selects best quality

Example:
```
Choose quality number: 2
[SELECTED] 720p
```

#### Step 4: Choose Download Folder

```
Enter download folder path:
(Leave empty to use current directory)
> 
```

**Options:**

Leave empty to save in current folder:
```
> [just press Enter]
[USING] Current directory: F:\projects\videocode
```

Or specify a custom path:

Windows example:
```
> C:\Users\YourName\Videos
[USING] Download folder: C:\Users\YourName\Videos
```

Linux/Mac example:
```
> /home/username/videos
[USING] Download folder: /home/username/videos
```

**The folder will be created automatically if it doesn't exist.**

#### Step 5: Download Starts

```
======================================================================
  STARTING DOWNLOAD
======================================================================

[SPEED BOOST] Using aria2c (16 parallel connections)

[DOWNLOADING] Your Video Title Here
[SAVING TO] C:\Users\YourName\Videos

Progress:   45.32% | Speed:   8.52 MB/s | ETA:  12s
```

**Progress indicators:**
- **Progress %** - Percentage downloaded
- **Speed** - Current download speed in MB/s
- **ETA** - Estimated time remaining in seconds

#### Step 6: Download Complete

```
[PROCESSING] Finalizing download...

======================================================================
  DOWNLOAD COMPLETE!
======================================================================

[SUCCESS] Video saved to:
  C:\Users\YourName\Videos\Your Video Title Here.mp4

[FILE SIZE] 65.20 MB

======================================================================
```

Your video is now ready to watch!

---

## Advanced Usage

### Downloading Multiple Videos

Run the script multiple times. Each time:
1. Enter new URL
2. Choose quality
3. Choose folder
4. Download

### Organizing Downloads

Create organized folders:

```
Videos/
  ├── Music/
  ├── Tutorials/
  ├── Entertainment/
  └── Education/
```

When downloading, specify the subfolder:
```
Enter download folder path:
> C:\Users\YourName\Videos\Tutorials
```

### Batch Downloading

For multiple videos, create a simple script:

**Windows (download_list.bat):**
```batch
@echo off
python downloader.py
pause
python downloader.py
pause
python downloader.py
pause
```

**Linux/Mac (download_list.sh):**
```bash
#!/bin/bash
python downloader.py
python downloader.py
python downloader.py
```

---

## Speed Optimization

### Maximum Speed Checklist

✅ **1. Install aria2c**
- Without: 1-3 MB/s
- With: 10-20+ MB/s
- **5-15x faster!**

✅ **2. Use Wired Connection**
- Ethernet is faster and more stable than Wi-Fi

✅ **3. Choose Optimal Quality**
- 1080p: Highest quality, slowest download
- 720p: **Best balance** (recommended)
- 480p: Fastest download

✅ **4. Close Bandwidth-Heavy Apps**
- Stop other downloads
- Pause streaming services
- Close online games

✅ **5. Download During Off-Peak Hours**
- Late night / early morning = faster
- Avoid 6-10 PM peak times

### Speed Comparison Table

| Configuration | Typical Speed | 100 MB Video |
|---------------|---------------|--------------|
| No aria2c, Wi-Fi, 1080p | 1-2 MB/s | ~60 seconds |
| No aria2c, Ethernet, 720p | 2-4 MB/s | ~30 seconds |
| **aria2c, Ethernet, 720p** | **10-20 MB/s** | **~6 seconds** |

### How aria2c Works

**Without aria2c:**
```
[YouTube Server] ──────────► [Your Computer]
     (1 connection)
```

**With aria2c:**
```
[YouTube Server] ══════════► [Your Computer]
[YouTube Server] ══════════► [Your Computer]
[YouTube Server] ══════════► [Your Computer]
    ... (16 connections total)
```

Multiple connections = **much faster downloads**!

---

## Troubleshooting

### Installation Issues

#### "python: command not found"

**Cause:** Python not installed or not in PATH

**Solution:**
1. Reinstall Python from [python.org](https://www.python.org/downloads/)
2. Check "Add Python to PATH" during installation
3. Restart terminal/command prompt

**Verify:** `python --version`

#### "No module named 'yt_dlp'"

**Cause:** Dependencies not installed

**Solution:**
```bash
pip install -r requirements.txt
```

Or directly:
```bash
pip install yt-dlp
```

#### "pip: command not found"

**Cause:** pip not installed

**Solution:**
```bash
# Windows
python -m ensurepip --upgrade

# Linux
sudo apt install python3-pip

# Mac
python3 -m ensurepip --upgrade
```

### Download Issues

#### Slow Downloads (1-3 MB/s)

**Cause:** aria2c not installed

**Solution:** Install aria2c (see [Installation Guide](#step-4-install-aria2c-optional-but-recommended))

**Verify:** `aria2c --version`

#### "Invalid YouTube URL"

**Cause:** URL format not recognized

**Supported:**
- ✅ `https://youtube.com/watch?v=VIDEO_ID`
- ✅ `https://youtu.be/VIDEO_ID`
- ✅ `https://youtube.com/shorts/VIDEO_ID`

**Not supported:**
- ❌ Playlists
- ❌ Channel URLs
- ❌ Other video sites

#### "No MP4 formats available"

**Cause:** Video doesn't have MP4 format

**Possible reasons:**
- Very old video
- Live stream
- Premiere (not yet released)

**Solution:** Try a different video

#### "Video is unavailable or removed"

**Possible causes:**
- Video deleted by creator
- Video is private
- Video is age-restricted
- Video is region-locked
- Copyright takedown

**Solution:** Try a different public video

#### "Video is DRM-protected"

**Cause:** Video has digital rights management (premium content)

**Examples:**
- YouTube Premium exclusive content
- Paid movies/shows

**Solution:** This tool only works with free, public YouTube videos

#### "Network timeout - connection too slow"

**Causes:**
- Slow internet
- Network congestion
- ISP throttling

**Solutions:**
1. Install aria2c (better reliability)
2. Use wired connection
3. Try again later
4. Choose lower quality (480p)
5. Check internet speed: [speedtest.net](https://www.speedtest.net/)

#### "Invalid download folder"

**Causes:**
- Folder path has typos
- No write permission
- Disk full

**Solutions:**

Use absolute path:
```
# Good
C:\Users\YourName\Videos

# Bad
..\Videos
```

Or leave empty to use current directory.

Check disk space:
```bash
# Windows
dir C:\

# Linux/Mac
df -h
```

#### Download stops at 99%

**Cause:** yt-dlp is processing/finalizing the file

**Solution:** Wait a few seconds. This is normal:
```
[PROCESSING] Finalizing download...
```

yt-dlp verifies the download and processes metadata.

### Runtime Errors

#### "UnicodeEncodeError"

**Cause:** Terminal encoding issue (especially on Windows)

**Solution:** The script handles this automatically. If issues persist:

Windows:
```cmd
chcp 65001
python downloader.py
```

#### "PermissionError"

**Cause:** No write permission to download folder

**Solution:**
1. Choose a different folder
2. Run as administrator (Windows)
3. Check folder permissions

#### "OSError: [Errno 28] No space left on device"

**Cause:** Disk is full

**Solution:**
1. Free up disk space
2. Choose a different drive
3. Delete old files

---

## FAQ

### General Questions

**Q: Is this tool legal?**  
A: Use only for personal purposes and videos you have permission to download. Respect copyright laws and YouTube's Terms of Service.

**Q: Does it work without internet?**  
A: No, you need internet to download from YouTube. But the tool itself runs locally.

**Q: Is my data safe?**  
A: Yes! Everything runs locally on your computer. No data is sent to external servers (except YouTube for downloading).

**Q: Can others see what I download?**  
A: No. There's no tracking, no logging, no cloud storage.

### Features

**Q: Can I download playlists?**  
A: Not currently. Download videos one at a time.

**Q: Can I download from other sites (Vimeo, Dailymotion, etc.)?**  
A: No, this tool is YouTube-only.

**Q: Can I download live streams?**  
A: No, only regular videos.

**Q: Can I download 4K/8K videos?**  
A: Yes, if the video has 4K/8K MP4 format available.

**Q: Can I download audio only?**  
A: This tool downloads video files (MP4). You can extract audio using other tools.

### Technical Questions

**Q: Why do I need aria2c?**  
A: aria2c enables parallel downloading (16 simultaneous connections), making downloads 5-15x faster.

**Q: How much faster is aria2c?**  
A: Typically 5-15x faster. Example: 100 MB video downloads in ~6 seconds instead of ~60 seconds.

**Q: Does aria2c work on all operating systems?**  
A: Yes - Windows, Linux, and macOS.

**Q: What if aria2c is not available?**  
A: The downloader automatically falls back to high-performance yt-dlp mode (still fast, but not as fast as aria2c).

**Q: Can I cancel a download?**  
A: Yes, press `Ctrl+C` (or `Cmd+C` on Mac).

**Q: Where are videos saved?**  
A: You choose the folder each time, or leave empty for current directory.

**Q: Can I rename the file?**  
A: The file is automatically named after the video title (sanitized for safety).

**Q: What if two videos have the same title?**  
A: The second file will overwrite the first. Organize downloads in different folders to avoid this.

### Troubleshooting

**Q: Why is my download slow?**  
A: Install aria2c. Without it, downloads are limited to single-connection mode.

**Q: Why do some videos have no audio?**  
A: Some formats are video-only. Choose a format with "[with audio]" indicator.

**Q: What does "video only" mean?**  
A: The format has no audio track. These are rare - most formats include audio.

**Q: Can I download age-restricted videos?**  
A: Usually no, unless you're logged into YouTube (this tool doesn't support login).

**Q: Why does it say "DRM-protected"?**  
A: The video has digital rights management and can't be downloaded (e.g., premium content).

---

## Tips & Tricks

### Choosing the Right Quality

**For watching on phone:**
- 480p or 720p (saves space)

**For watching on computer:**
- 720p or 1080p (good quality)

**For archiving:**
- Best quality available (highest resolution)

**For quick preview:**
- 480p (fastest download)

### Folder Organization Tips

Create a structured folder system:

```
MyVideos/
  ├── Education/
  │   ├── Programming/
  │   ├── Science/
  │   └── Languages/
  ├── Entertainment/
  │   ├── Music/
  │   ├── Comedy/
  │   └── Gaming/
  └── Work/
      ├── Tutorials/
      └── Presentations/
```

### Speed Optimization Tips

1. **Close background apps** before downloading
2. **Pause cloud sync** (OneDrive, Dropbox, Google Drive)
3. **Disable VPN** if not needed (can slow downloads)
4. **Use Task Manager** to check network usage
5. **Restart router** if connection is slow

### Keyboard Shortcuts

- `Ctrl+C` (or `Cmd+C`) - Cancel download
- `Ctrl+V` (or `Cmd+V`) - Paste URL
- `Enter` - Submit input

### Updating the Tool

Keep yt-dlp updated (YouTube changes frequently):

```bash
pip install --upgrade yt-dlp
```

Recommended: Update every 1-2 weeks.

---

## Getting More Help

### Check Logs

If downloads fail, check the error message carefully. The tool provides detailed error information.

### Update yt-dlp

Many issues are fixed by updating:

```bash
pip install --upgrade yt-dlp
```

### Test Your Internet

Visit [speedtest.net](https://www.speedtest.net/) to check your connection speed.

### Report Issues

If you found a bug:
1. Note the exact error message
2. Note the video URL (if shareable)
3. Note your OS and Python version
4. Create an issue on GitHub

---

**Happy downloading! 🎥⚡**

**Remember:** 
- ✅ Install aria2c for maximum speed
- ✅ Use 720p for best balance
- ✅ Choose organized folders
- ✅ Keep yt-dlp updated
