# YouTube Video Downloader

This repository contains scripts for downloading YouTube videos:

1. `youtube_downloader.py` - Uses the `pytube` library (may have issues with some videos)
2. `youtube_downloader_yt_dlp.py` - Uses the more robust `yt-dlp` library (recommended)
3. `download_video.bat` - Windows batch file for easy execution
4. `download_video.ps1` - PowerShell script for easy execution
5. `youtube_downloader_gui.py` - User-friendly GUI application (recommended for beginners)
6. `launch_youtube_downloader.bat` - Batch file to launch the GUI application
7. `launch_youtube_downloader.ps1` - PowerShell script to launch the GUI application

## Prerequisites

- Python 3.6 or higher
- Required libraries: `pytube` and/or `yt-dlp`

## Installation

```bash
# Install pytube (for youtube_downloader.py)
py -m pip install pytube

# Install yt-dlp (for youtube_downloader_yt_dlp.py - recommended)
py -m pip install yt-dlp
```

## Usage

### GUI Application (Recommended for Beginners)

For the easiest experience, use the GUI application:

```
# Using Command Prompt
.\launch_youtube_downloader.bat

# Using PowerShell
powershell -ExecutionPolicy Bypass -File .\launch_youtube_downloader.ps1
```

The GUI application provides:
1. User-friendly interface with buttons and input fields
2. Progress bar for download tracking
3. Download queue for multiple videos
4. Format and quality selection options
5. Directory browser for selecting download location

### Command Line Usage (Windows)

For command line usage, use one of the provided convenience scripts:

```
# Using Command Prompt
.\download_video.bat

# Using PowerShell
powershell -ExecutionPolicy Bypass -File .\download_video.ps1
```

These scripts will:
1. Check if Python is installed
2. Install yt-dlp if needed
3. Prompt for YouTube URL and download location
4. Download the video

### Basic Usage (Python Scripts)

Run either script and follow the prompts:

```bash
# Using pytube version
py youtube_downloader.py

# Using yt-dlp version (recommended)
py youtube_downloader_yt_dlp.py
```

You'll be prompted to enter:
1. YouTube video URL
2. Download directory (optional, defaults to `F:\temp\New folder`)

### Command Line Arguments (yt-dlp version only)

The `youtube_downloader_yt_dlp.py` script supports command line arguments:

```bash
py youtube_downloader_yt_dlp.py [URL] [-o OUTPUT_DIR] [-f FORMAT] [-q QUALITY] [--debug]
```

Options:
- `URL`: YouTube video URL
- `-o, --output`: Output directory (default: `F:\temp\New folder`)
- `-f, --format`: Video format like mp4, webm (default: mp4)
- `-q, --quality`: Video quality like best, worst (default: best)
- `--debug`: Enable debug mode for detailed information

Examples:

```bash
# Download a video in mp4 format with best quality
py youtube_downloader_yt_dlp.py https://www.youtube.com/watch?v=dQw4w9WgXcQ

# Download a video in webm format to a specific directory
py youtube_downloader_yt_dlp.py https://www.youtube.com/watch?v=dQw4w9WgXcQ -f webm -o "C:\Downloads"

# Download with debug information
py youtube_downloader_yt_dlp.py https://www.youtube.com/watch?v=dQw4w9WgXcQ --debug
```

## Features

### youtube_downloader_gui.py (GUI Application)
- User-friendly graphical interface
- Progress bar with percentage display
- Download queue for multiple videos
- Format selection (mp4, webm, audio only)
- Quality selection (best, medium, worst)
- Directory browser for selecting download location
- Status updates during download
- Works with both yt-dlp and pytube (prefers yt-dlp)

### youtube_downloader.py (pytube)
- Downloads highest resolution video available
- Shows download progress
- Handles common errors
- Allows custom download location
- Supports downloading multiple videos in a loop

### youtube_downloader_yt_dlp.py (recommended)
- More reliable downloading from YouTube
- Better error handling
- Detailed progress information
- Supports downloading multiple videos in a loop
- Command line argument support
- Format and quality selection
- Debug mode for troubleshooting

## Troubleshooting

### pytube version
- If you get SSL errors, update pytube: `py -m pip install --upgrade pytube`
- For age-restricted videos, you may need additional authentication (not supported)

### yt-dlp version
- Run with `--debug` flag for detailed error information
- Update yt-dlp regularly: `py -m pip install --upgrade yt-dlp`

## Legal Note

Only download videos you have permission to download. Check YouTube's terms of service for more information.