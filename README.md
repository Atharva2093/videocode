# YouTube Video Downloader

A simple and reliable YouTube video downloader built with **Python**. It provides both a **Graphical User Interface (GUI)** for beginners and a **Command-Line Interface (CLI)** for advanced users. The downloader primarily uses **yt-dlp** for reliable downloads, with **pytube** as an optional fallback. Supports multiple formats (mp4, webm, mp3) and quality options, and allows batch downloads.

---

## Features

### GUI Application
- Easy-to-use interface
- Download queue for multiple videos
- Select video format (mp4/webm) or audio-only (mp3)
- Choose quality: best, medium, worst
- Select download folder
- Progress bar and status updates

### Command-Line Interface
- Interactive mode for multiple downloads
- Pass arguments for URL, output folder, format, quality
- Debug mode for troubleshooting

### Reliable Backend
- **yt-dlp** (recommended)
- **pytube** (optional)

---

## Prerequisites

- Python 3.6 or higher
- Libraries:
  - `yt-dlp` (recommended)
  - `pytube` (optional)
  - `tkinter` (usually included on Windows)
- `ffmpeg` required for mp3 extraction (yt-dlp may prompt to download)

---

## 📥 Installation (Super Easy!)

### Step 1: Open Command Prompt
1. Press `Windows Key + R` on your keyboard
2. Type `cmd` and press Enter
3. A black window will open - this is Command Prompt

### Step 2: Install the Required Software
Copy and paste this command into the black window, then press Enter:
```bash
py -m pip install yt-dlp
```
Wait for it to finish downloading and installing. You'll see text scrolling - that's normal!

### Step 3: Verify Installation
Type this command to check if everything installed correctly:
```bash
py -c "import yt_dlp; print('✅ yt-dlp installed successfully!')"
```

If you see the green checkmark message, you're ready to go!

---

## 🚀 How to Use (Beginner-Friendly!)

### Method 1: Using the Easy GUI App (RECOMMENDED FOR BEGINNERS)

#### Step 1: Get the App Running
**Option A - Double-click method (Easiest):**
1. Find the file called `launch_youtube_downloader.bat` in your downloaded folder
2. Double-click on it
3. A window should pop up - this is your downloader!

**Option B - If double-click doesn't work:**
1. Right-click on `launch_youtube_downloader.bat`
2. Select "Run as administrator"
3. Click "Yes" when Windows asks for permission

**Option C - Manual method:**
1. Open Command Prompt (same as Step 1 in installation)
2. Type: `cd` followed by a space, then drag your downloaded folder into the window
3. Press Enter
4. Type: `launch_youtube_downloader.bat`
5. Press Enter

#### Step 2: Start Downloading Videos! 🎬

Once the app window opens, follow these simple steps:

1. **Copy a YouTube URL:**
   - Go to YouTube in your web browser
   - Find the video you want to download
   - Copy the URL from your browser's address bar (Ctrl+C)

2. **Paste the URL:**
   - Click in the text box that says "Enter YouTube URL here"
   - Paste the URL (Ctrl+V)

3. **Choose where to save:**
   - Click the "Browse" button
   - Select the folder where you want your video saved
   - Click "Select Folder"

4. **Pick your settings:**
   - **Format:** Choose MP4 (for video) or MP3 (for audio only)
   - **Quality:** Choose "Best" for highest quality, "Medium" for balanced, or "Worst" for smallest file

5. **Download:**
   - Click the big "Download" button
   - Wait for the progress bar to complete
   - Your video will be saved in the folder you chose!

#### 🎯 Quick Tips:
- ✅ You can download multiple videos by repeating steps 1-5
- ✅ The app will show you a list of all your downloads
- ✅ If something goes wrong, check the status messages at the bottom
- ✅ Close the app when you're done by clicking the X button

---

### Method 2: Command Line (For Advanced Users Only)

If you're comfortable with Command Prompt, you can also use text commands:

#### Interactive Mode:
```bash
py youtube_downloader_yt_dlp.py
```
1. Enter the download folder path.
2. Enter video URLs one by one.
3. Type `exit` to finish.

#### Single-Use Mode with Arguments:
```bash
py youtube_downloader_yt_dlp.py [URL] [-o OUTPUT_DIR] [-f FORMAT] [-q QUALITY] [--debug]
```

**Options:**
- `URL` – YouTube video link
- `-o, --output` – Folder to save video (default: F:\temp\New folder)
- `-f, --format` – Video format (mp4, webm, mp3)
- `-q, --quality` – Video quality (best, medium, worst)
- `--debug` – Show detailed error messages

#### Examples:
```bash
# Download video with default settings
py youtube_downloader_yt_dlp.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

# Download in webm format to a specific folder
py youtube_downloader_yt_dlp.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ" -o "C:\Downloads" -f webm

# Download with debug information
py youtube_downloader_yt_dlp.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ" --debug
```

---

## Troubleshooting

1. **Update libraries:**
   ```bash
   py -m pip install --upgrade yt-dlp
   py -m pip install --upgrade pytube
   ```

2. Ensure `ffmpeg` is installed for mp3 audio extraction.

3. Use `--debug` in CLI for detailed errors.

4. If using pytube and getting SSL errors, update pytube:
   ```bash
   py -m pip install --upgrade pytube
   ```

---

## Legal Disclaimer

This tool is intended for personal use only. Respect copyright laws and YouTube's terms of service. Do not download content you are not authorized to access.
