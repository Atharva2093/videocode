# YouTube Video Downloader PowerShell Script

Write-Host "YouTube Video Downloader" -ForegroundColor Cyan
Write-Host "========================" -ForegroundColor Cyan
Write-Host ""

# Check if Python is installed
try {
    $pythonVersion = py --version
    Write-Host "Found Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "Error: Python is not installed or not in PATH." -ForegroundColor Red
    Write-Host "Please install Python from https://www.python.org/downloads/" -ForegroundColor Yellow
    Write-Host "Make sure to check 'Add Python to PATH' during installation." -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if yt-dlp is installed
try {
    py -c "import yt_dlp" | Out-Null
    Write-Host "yt-dlp is already installed." -ForegroundColor Green
} catch {
    Write-Host "Installing yt-dlp..." -ForegroundColor Yellow
    py -m pip install yt-dlp
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Error: Failed to install yt-dlp." -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
    Write-Host "yt-dlp installed successfully." -ForegroundColor Green
}

# Get output directory first (only once)
$OUTPUT = Read-Host "Enter download path (or press Enter for default directory)"

# Use default directory if none provided
if ([string]::IsNullOrWhiteSpace($OUTPUT)) {
    $OUTPUT = "F:\temp\New folder"
}

# Get video URL
$URL = Read-Host "Enter YouTube video URL (or press Enter to use default)"

# Use default URL if none provided
if ([string]::IsNullOrWhiteSpace($URL)) {
    $URL = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    Write-Host "Using default URL: $URL" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Downloading video..." -ForegroundColor Cyan
Write-Host ""

# Run the downloader script (it now handles the loop internally)
py youtube_downloader_yt_dlp.py "$URL" -o "$OUTPUT"