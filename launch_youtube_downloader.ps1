# YouTube Downloader GUI Launcher
Write-Host "Starting YouTube Downloader GUI..." -ForegroundColor Cyan

# Check if Python is installed (try both python and py commands)
$pythonCmd = $null

try {
    $pythonVersion = python --version 2>&1
    Write-Host "Found $pythonVersion" -ForegroundColor Green
    $pythonCmd = "python"
} catch {
    Write-Host "Python command not found, trying py..." -ForegroundColor Yellow
    
    try {
        $pythonVersion = py --version 2>&1
        Write-Host "Found $pythonVersion" -ForegroundColor Green
        $pythonCmd = "py"
    } catch {
        Write-Host "Python is not installed or not in PATH. Please install Python 3.x" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
}

# Check if required packages are installed
try {
    & $pythonCmd -c "import tkinter" | Out-Null
    Write-Host "tkinter is available" -ForegroundColor Green
} catch {
    Write-Host "tkinter is not available. Please install Python with tkinter support." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Try to import yt-dlp or pytube
$downloaderFound = $false

try {
    & $pythonCmd -c "import yt_dlp" | Out-Null
    Write-Host "yt-dlp is installed" -ForegroundColor Green
    $downloaderFound = $true
} catch {
    Write-Host "yt-dlp is not installed" -ForegroundColor Yellow
}

if (-not $downloaderFound) {
    try {
        & $pythonCmd -c "from pytube import YouTube" | Out-Null
        Write-Host "pytube is installed" -ForegroundColor Green
        $downloaderFound = $true
    } catch {
        Write-Host "pytube is not installed" -ForegroundColor Yellow
    }
}

if (-not $downloaderFound) {
    Write-Host "Neither yt-dlp nor pytube is installed." -ForegroundColor Yellow
    $installChoice = Read-Host "Would you like to install yt-dlp? (y/n)"
    
    if ($installChoice -eq "y") {
        Write-Host "Installing yt-dlp..." -ForegroundColor Cyan
        try {
            & $pythonCmd -m pip install yt-dlp
            Write-Host "yt-dlp installed successfully" -ForegroundColor Green
        } catch {
            Write-Host "Failed to install yt-dlp. Please install it manually:" -ForegroundColor Red
            Write-Host "$pythonCmd -m pip install yt-dlp" -ForegroundColor Yellow
            Read-Host "Press Enter to exit"
            exit 1
        }
    } else {
        Write-Host "Please install either yt-dlp or pytube manually:" -ForegroundColor Yellow
        Write-Host "$pythonCmd -m pip install yt-dlp" -ForegroundColor Yellow
        Write-Host "or" -ForegroundColor Yellow
        Write-Host "$pythonCmd -m pip install pytube" -ForegroundColor Yellow
        Read-Host "Press Enter to exit"
        exit 1
    }
}

# Launch the GUI application
Write-Host "Launching YouTube Downloader GUI with $pythonCmd..." -ForegroundColor Cyan
try {
    & $pythonCmd youtube_downloader_gui.py
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Error launching the GUI application (Exit code: $LASTEXITCODE)" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
} catch {
    Write-Host "Error launching the GUI application: $_" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}