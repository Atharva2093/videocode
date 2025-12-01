/* ========================================
   YOUTUBE DOWNLOADER - FRONTEND SCRIPT
   Clean, modular, step-by-step workflow
======================================== */

// ========================================
// CONFIGURATION
// ========================================
const API = location.hostname.includes("localhost") || location.hostname.includes("127.")
    ? "http://127.0.0.1:8000/api"
    : "https://yt-downloader-backend-ogpx.onrender.com/api";

// ========================================
// STATE
// ========================================
let selectedFormat = "mp4";
let selectedQuality = null;
let currentVideoData = null;
let currentVideoUrl = "";
let selectedFolder = null;
let availableQualities = [];

// ========================================
// DOM ELEMENTS
// ========================================
const urlInput = document.getElementById("urlInput");
const fetchBtn = document.getElementById("fetchBtn");
const loader = document.getElementById("loader");
const errorBox = document.getElementById("errorBox");
const errorMessage = document.getElementById("errorMessage");
const errorHint = document.getElementById("errorHint");
const videoPreview = document.getElementById("videoPreview");
const thumbnail = document.getElementById("thumbnail");
const videoTitle = document.getElementById("videoTitle");
const videoChannel = document.getElementById("videoChannel");
const videoDuration = document.getElementById("videoDuration");
const qualitySection = document.getElementById("qualitySection");
const qualityChips = document.getElementById("qualityChips");
const downloadSection = document.getElementById("downloadSection");
const folderBtn = document.getElementById("folderBtn");
const folderStatus = document.getElementById("folderStatus");
const downloadBtn = document.getElementById("downloadBtn");
const progressSection = document.getElementById("progressSection");
const progressFill = document.getElementById("progressFill");
const progressText = document.getElementById("progressText");
const successBox = document.getElementById("successBox");
const recentList = document.getElementById("recentList");
const connectionStatus = document.getElementById("connectionStatus");

// ========================================
// INITIALIZATION
// ========================================
document.addEventListener("DOMContentLoaded", () => {
    checkConnection();
    renderRecentDownloads();
    setupEventListeners();
    checkFolderPickerSupport();
});

function setupEventListeners() {
    // Clear errors on input
    urlInput.addEventListener("input", () => {
        hideError();
        hideSuccess();
    });
    
    // Enter key to fetch
    urlInput.addEventListener("keypress", (e) => {
        if (e.key === "Enter") fetchVideo();
    });
}

function checkFolderPickerSupport() {
    if (window.showDirectoryPicker) {
        folderBtn.classList.remove("hidden");
    }
}

// ========================================
// THEME TOGGLE
// ========================================
function toggleTheme() {
    const html = document.documentElement;
    const newTheme = html.dataset.theme === "dark" ? "light" : "dark";
    html.dataset.theme = newTheme;
    
    const icon = document.querySelector(".theme-icon");
    icon.textContent = newTheme === "dark" ? "☀️" : "🌙";
    
    localStorage.setItem("theme", newTheme);
}

// Load saved theme
(function() {
    const saved = localStorage.getItem("theme");
    if (saved) {
        document.documentElement.dataset.theme = saved;
        const icon = document.querySelector(".theme-icon");
        if (icon) icon.textContent = saved === "dark" ? "☀️" : "🌙";
    }
})();

// ========================================
// CLIPBOARD
// ========================================
async function pasteFromClipboard() {
    try {
        const text = await navigator.clipboard.readText();
        if (text && isYouTubeUrl(text)) {
            urlInput.value = cleanUrl(text);
            hideError();
        } else if (text) {
            urlInput.value = text;
        }
    } catch (err) {
        // Clipboard access denied - silent fail
    }
}

// ========================================
// URL VALIDATION & CLEANING
// ========================================
function isYouTubeUrl(url) {
    return /(?:youtube\.com|youtu\.be)/.test(url);
}

function cleanUrl(url) {
    try {
        const urlObj = new URL(url);
        // Remove tracking parameters
        const paramsToRemove = ["si", "feature", "t", "start", "list", "index"];
        paramsToRemove.forEach(p => urlObj.searchParams.delete(p));
        return urlObj.toString();
    } catch {
        return url;
    }
}

function validateUrl(url) {
    if (!url) {
        return { valid: false, message: "Please enter a URL", hint: "" };
    }
    
    if (!isYouTubeUrl(url)) {
        return { 
            valid: false, 
            message: "Invalid YouTube URL", 
            hint: "Example: https://youtube.com/watch?v=..." 
        };
    }
    
    return { valid: true };
}

// ========================================
// FORMAT SELECTION
// ========================================
function setFormat(format) {
    selectedFormat = format;
    
    document.getElementById("btnMp4").classList.toggle("active", format === "mp4");
    document.getElementById("btnMp3").classList.toggle("active", format === "mp3");
    
    // Show/hide quality section based on format
    if (currentVideoData) {
        if (format === "mp4" && availableQualities.length > 0) {
            qualitySection.classList.remove("hidden");
        } else {
            qualitySection.classList.add("hidden");
        }
    }
}

// ========================================
// QUALITY SELECTION
// ========================================
function setQuality(quality) {
    selectedQuality = quality;
    
    document.querySelectorAll(".quality-chip").forEach(chip => {
        chip.classList.toggle("active", chip.dataset.quality === quality);
    });
}

function renderQualityChips(formats) {
    const qualitySet = new Set();
    
    formats.forEach(f => {
        if (f.height) {
            qualitySet.add(f.height);
        }
    });
    
    availableQualities = Array.from(qualitySet).sort((a, b) => b - a);
    
    if (availableQualities.length === 0) {
        qualitySection.classList.add("hidden");
        return;
    }
    
    // Default to 720p or highest available
    selectedQuality = availableQualities.includes(720) ? 720 : availableQualities[0];
    
    qualityChips.innerHTML = availableQualities.map(q => `
        <button 
            class="quality-chip ${q === selectedQuality ? 'active' : ''}" 
            data-quality="${q}"
            onclick="setQuality(${q})"
        >
            ${q}p
        </button>
    `).join("");
}

// ========================================
// FETCH VIDEO INFO
// ========================================
async function fetchVideo() {
    const url = urlInput.value.trim();
    
    // Validate
    const validation = validateUrl(url);
    if (!validation.valid) {
        showError(validation.message, validation.hint);
        return;
    }
    
    // Clean URL
    const cleanedUrl = cleanUrl(url);
    urlInput.value = cleanedUrl;
    currentVideoUrl = cleanedUrl;
    
    // Reset UI
    resetUI();
    showLoader();
    
    try {
        const res = await fetch(`${API}/metadata?url=${encodeURIComponent(cleanedUrl)}`);
        const data = await res.json();
        
        hideLoader();
        
        if (data.error) {
            showError(data.message || data.error, data.hint || "");
            return;
        }
        
        currentVideoData = data;
        displayVideoInfo(data);
        
    } catch (err) {
        hideLoader();
        showError("Connection failed", "Check your internet or try again later");
    }
}

function displayVideoInfo(data) {
    // Set thumbnail
    thumbnail.src = data.thumbnail || "";
    
    // Set title
    videoTitle.textContent = data.title || "Unknown Title";
    
    // Set channel (if available)
    videoChannel.textContent = data.channel || data.uploader || "";
    
    // Set duration
    if (data.duration) {
        const mins = Math.floor(data.duration / 60);
        const secs = data.duration % 60;
        videoDuration.textContent = `${mins}:${secs.toString().padStart(2, '0')}`;
    } else {
        videoDuration.textContent = "";
    }
    
    // Show video preview
    videoPreview.classList.remove("hidden");
    
    // Render quality chips for MP4
    if (data.formats && data.formats.length > 0) {
        renderQualityChips(data.formats);
        if (selectedFormat === "mp4") {
            qualitySection.classList.remove("hidden");
        }
    }
    
    // Show download section
    downloadSection.classList.remove("hidden");
}

// ========================================
// FOLDER PICKER
// ========================================
async function selectFolder() {
    if (!window.showDirectoryPicker) {
        return;
    }
    
    try {
        selectedFolder = await window.showDirectoryPicker();
        folderStatus.textContent = "📁 Folder selected";
        folderStatus.classList.remove("hidden");
    } catch (err) {
        // User cancelled - silent
    }
}

// ========================================
// DOWNLOAD
// ========================================
async function startDownload() {
    if (!currentVideoUrl) return;
    
    hideError();
    hideSuccess();
    showProgress();
    
    const formatId = selectedFormat === "mp3" 
        ? "mp3" 
        : `best[height<=${selectedQuality || 720}]`;
    
    const downloadUrl = `${API}/download?url=${encodeURIComponent(currentVideoUrl)}&format_id=${encodeURIComponent(formatId)}`;
    
    // Simulate progress
    let progress = 0;
    const interval = setInterval(() => {
        if (progress < 90) {
            progress += Math.random() * 15;
            updateProgress(Math.min(progress, 90));
        }
    }, 300);
    
    try {
        if (selectedFolder) {
            // Download to selected folder
            const response = await fetch(downloadUrl);
            
            // Check for error response
            const contentType = response.headers.get("content-type");
            if (contentType && contentType.includes("application/json")) {
                const data = await response.json();
                clearInterval(interval);
                hideProgress();
                showError(data.message || data.error, data.hint || "");
                return;
            }
            
            const blob = await response.blob();
            const fileName = getFileName(response, currentVideoData?.title);
            
            const fileHandle = await selectedFolder.getFileHandle(fileName, { create: true });
            const writable = await fileHandle.createWritable();
            await writable.write(blob);
            await writable.close();
            
            clearInterval(interval);
            updateProgress(100);
            
            setTimeout(() => {
                hideProgress();
                showSuccess();
                saveToHistory(currentVideoData?.title || currentVideoUrl);
            }, 500);
            
        } else {
            // Browser download
            clearInterval(interval);
            updateProgress(100);
            
            setTimeout(() => {
                hideProgress();
                showSuccess();
                saveToHistory(currentVideoData?.title || currentVideoUrl);
                window.location.href = downloadUrl;
            }, 500);
        }
        
    } catch (err) {
        clearInterval(interval);
        hideProgress();
        showError("Download failed", "Please try again");
    }
}

function getFileName(response, title) {
    const contentDisposition = response.headers.get("content-disposition");
    if (contentDisposition) {
        const match = contentDisposition.match(/filename="?([^"]+)"?/);
        if (match) return match[1];
    }
    
    const ext = selectedFormat === "mp3" ? ".mp3" : ".mp4";
    const safeName = (title || "video").replace(/[^a-zA-Z0-9]/g, "_").substring(0, 50);
    return safeName + ext;
}

// ========================================
// PROGRESS
// ========================================
function showProgress() {
    progressSection.classList.remove("hidden");
    updateProgress(0);
}

function hideProgress() {
    progressSection.classList.add("hidden");
}

function updateProgress(percent) {
    progressFill.style.width = percent + "%";
    progressText.textContent = Math.round(percent) + "%";
}

// ========================================
// ERROR HANDLING
// ========================================
function showError(message, hint = "") {
    errorMessage.textContent = message;
    errorHint.textContent = hint;
    errorBox.classList.remove("hidden");
}

function hideError() {
    errorBox.classList.add("hidden");
}

// ========================================
// SUCCESS MESSAGE
// ========================================
function showSuccess() {
    successBox.classList.remove("hidden");
}

function hideSuccess() {
    successBox.classList.add("hidden");
}

// ========================================
// LOADER
// ========================================
function showLoader() {
    loader.classList.remove("hidden");
    fetchBtn.disabled = true;
}

function hideLoader() {
    loader.classList.add("hidden");
    fetchBtn.disabled = false;
}

// ========================================
// RESET UI
// ========================================
function resetUI() {
    hideError();
    hideSuccess();
    hideProgress();
    videoPreview.classList.add("hidden");
    qualitySection.classList.add("hidden");
    downloadSection.classList.add("hidden");
    currentVideoData = null;
    availableQualities = [];
}

// ========================================
// RECENT DOWNLOADS (localStorage)
// ========================================
function saveToHistory(title) {
    const history = JSON.parse(localStorage.getItem("downloadHistory") || "[]");
    
    history.unshift({
        title: title.substring(0, 60),
        time: new Date().toLocaleString()
    });
    
    // Keep only last 5
    if (history.length > 5) history.pop();
    
    localStorage.setItem("downloadHistory", JSON.stringify(history));
    renderRecentDownloads();
}

function renderRecentDownloads() {
    const history = JSON.parse(localStorage.getItem("downloadHistory") || "[]");
    
    if (history.length === 0) {
        recentList.innerHTML = '<p class="empty-text">No downloads yet</p>';
        return;
    }
    
    recentList.innerHTML = history.map(item => `
        <div class="recent-item">
            <span class="recent-item-title">${escapeHtml(item.title)}</span>
            <span class="recent-item-time">${item.time}</span>
        </div>
    `).join("");
}

function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}

// ========================================
// CONNECTION STATUS
// ========================================
async function checkConnection() {
    try {
        const res = await fetch(`${API}/health`);
        const data = await res.json();
        
        if (data.status === "ok") {
            connectionStatus.textContent = "● Connected";
            connectionStatus.classList.remove("offline");
            connectionStatus.classList.add("online");
        } else {
            throw new Error("Not ok");
        }
    } catch {
        connectionStatus.textContent = "● Offline";
        connectionStatus.classList.remove("online");
        connectionStatus.classList.add("offline");
    }
}

// Check connection every 30 seconds
setInterval(checkConnection, 30000);
