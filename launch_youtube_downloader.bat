@echo off
echo Starting YouTube Downloader GUI...

:: Check if Python is installed (try both python and py commands)
python --version >nul 2>&1
if %errorlevel% neq 0 (
    py --version >nul 2>&1
    if %errorlevel% neq 0 (
        echo Python is not installed or not in PATH. Please install Python 3.x
        pause
        exit /b 1
    ) else (
        set PYTHON_CMD=py
    )
) else (
    set PYTHON_CMD=python
)

:: Check if required packages are installed
%PYTHON_CMD% -c "import tkinter" >nul 2>&1
if %errorlevel% neq 0 (
    echo tkinter is not available. Please install Python with tkinter support.
    pause
    exit /b 1
)

:: Try to import yt-dlp or pytube
%PYTHON_CMD% -c "import yt_dlp" >nul 2>&1
if %errorlevel% neq 0 (
    %PYTHON_CMD% -c "from pytube import YouTube" >nul 2>&1
    if %errorlevel% neq 0 (
        echo Neither yt-dlp nor pytube is installed.
        echo Installing yt-dlp...
        %PYTHON_CMD% -m pip install yt-dlp
        if %errorlevel% neq 0 (
            echo Failed to install yt-dlp. Please install it manually:
            echo pip install yt-dlp
            pause
            exit /b 1
        )
    )
)

:: Launch the GUI application
echo Launching YouTube Downloader GUI with %PYTHON_CMD%...
%PYTHON_CMD% youtube_downloader_gui.py

if %errorlevel% neq 0 (
    echo Error launching the GUI application. Please check if Python and required packages are installed correctly.
    pause
    exit /b 1
)