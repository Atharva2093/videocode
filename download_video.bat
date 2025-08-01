@echo off
echo YouTube Video Downloader
echo ========================
echo.

REM Check if Python is installed
where py >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo Error: Python is not installed or not in PATH.
    echo Please install Python from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

REM Check if yt-dlp is installed
py -c "import yt_dlp" >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo Installing yt-dlp...
    py -m pip install yt-dlp
    if %ERRORLEVEL% neq 0 (
        echo Error: Failed to install yt-dlp.
        pause
        exit /b 1
    )
    echo yt-dlp installed successfully.
    echo.
)

REM Get output directory first (only once)
set /p OUTPUT="Enter download path (or press Enter for default directory): "

REM Use default directory if none provided
if "%OUTPUT%"=="" set OUTPUT=F:\temp\New folder

REM Get video URL
set /p URL="Enter YouTube video URL (or press Enter to use default): "

REM Use default URL if none provided
if "%URL%"=="" (
    set URL=https://www.youtube.com/watch?v=dQw4w9WgXcQ
    echo Using default URL: %URL%
)

echo.
echo Downloading video...
echo.

REM Run the downloader script (it now handles the loop internally)
py youtube_downloader_yt_dlp.py "%URL%" -o "%OUTPUT%"