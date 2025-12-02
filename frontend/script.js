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
let selectedFormatId = null;  // The actual format_id to send to backend
let currentVideoData = null;
let currentVideoUrl = "";
let qualityToFormatMap = {};  // Maps height -> best format_id for that height
let pendingDownloadFolder = null;  // Folder selected in modal

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
const downloadBtn = document.getElementById("downloadBtn");
const progressSection = document.getElementById("progressSection");
const progressFill = document.getElementById("progressFill");
const progressText = document.getElementById("progressText");
const successBox = document.getElementById("successBox");
const recentList = document.getElementById("recentList");
const connectionStatus = document.getElementById("connectionStatus");
const downloadModal = document.getElementById("downloadModal");

// ========================================
// INITIALIZATION
// ========================================
document.addEventListener("DOMContentLoaded", () => {
    checkConnection();
    renderRecentDownloads();
    setupEventListeners();
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
    
    // Close modal on overlay click
    if (downloadModal) {
        downloadModal.addEventListener("click", (e) => {
            if (e.target === downloadModal) hideDownloadModal();
        });
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
        if (format === "mp4" && Object.keys(qualityToFormatMap).length > 0) {
            qualitySection.classList.remove("hidden");
        } else {
            qualitySection.classList.add("hidden");
        }
    }
}

// ========================================
// QUALITY SELECTION
// ========================================
function setQuality(quality, formatId) {
    selectedQuality = quality;
    selectedFormatId = formatId;
    
    document.querySelectorAll(".quality-chip").forEach(chip => {
        chip.classList.toggle("active", parseInt(chip.dataset.quality) === quality);
    });
}

function renderQualityChips(videoFormats) {
    // Build a map of height -> best format for that height
    // Prefer formats with audio, then by filesize (larger = better quality)
    qualityToFormatMap = {};
    
    videoFormats.forEach(f => {
        if (!f.height) return;
        
        const height = f.height;
        const existing = qualityToFormatMap[height];
        
        if (!existing) {
            qualityToFormatMap[height] = f;
        } else {
            // Prefer format with audio
            if (f.has_audio && !existing.has_audio) {
                qualityToFormatMap[height] = f;
            }
            // If both have audio or both don't, prefer larger filesize
            else if (f.has_audio === existing.has_audio) {
                const fSize = f.filesize || 0;
                const eSize = existing.filesize || 0;
                if (fSize > eSize) {
                    qualityToFormatMap[height] = f;
                }
            }
        }
    });
    
    // Get sorted heights (highest first)
    const heights = Object.keys(qualityToFormatMap)
        .map(h => parseInt(h))
        .sort((a, b) => b - a);
    
    if (heights.length === 0) {
        qualitySection.classList.add("hidden");
        return;
    }
    
    // Default to 720p if available, else highest
    const defaultHeight = heights.includes(720) ? 720 : heights[0];
    selectedQuality = defaultHeight;
    selectedFormatId = qualityToFormatMap[defaultHeight].format_id;
    
    // Render chips
    qualityChips.innerHTML = heights.map(h => {
        const format = qualityToFormatMap[h];
        const sizeStr = format.filesize ? formatFileSize(format.filesize) : "";
        const fpsStr = format.fps && format.fps > 30 ? ` ${format.fps}fps` : "";
        const label = `${h}p${fpsStr}`;
        
        return `
            <button 
                class="quality-chip ${h === defaultHeight ? 'active' : ''}" 
                data-quality="${h}"
                data-format-id="${format.format_id}"
                onclick="setQuality(${h}, '${format.format_id}')"
                title="${sizeStr}"
            >
                ${label}
            </button>
        `;
    }).join("");
}

function formatFileSize(bytes) {
    if (!bytes) return "";
    const mb = bytes / (1024 * 1024);
    if (mb >= 1000) {
        return (mb / 1024).toFixed(1) + " GB";
    }
    return mb.toFixed(1) + " MB";
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
    videoChannel.textContent = data.channel || "";
    
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
    
    // Render quality chips for MP4 using the new video_formats array
    if (data.video_formats && data.video_formats.length > 0) {
        renderQualityChips(data.video_formats);
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
        return null;
    }
    
    try {
        return await window.showDirectoryPicker();
    } catch (err) {
        // User cancelled
        return null;
    }
}

// ========================================
// DOWNLOAD MODAL
// ========================================
function showDownloadModal() {
    // Only show folder option if browser supports it
    const folderBtn = document.getElementById("modalFolderBtn");
    if (folderBtn) {
        folderBtn.style.display = window.showDirectoryPicker ? "flex" : "none";
    }
    downloadModal.classList.remove("hidden");
}

function hideDownloadModal() {
    downloadModal.classList.add("hidden");
}

// Called when user clicks "Select Folder" in modal
async function handleFolderDownload() {
    hideDownloadModal();
    
    const folder = await selectFolder();
    if (!folder) {
        // User cancelled folder picker, do nothing
        return;
    }
    
    pendingDownloadFolder = folder;
    executeDownload(true);
}

// Called when user clicks "Download Normally" in modal
function handleNormalDownload() {
    hideDownloadModal();
    pendingDownloadFolder = null;
    executeDownload(false);
}

// ========================================
// DOWNLOAD - Entry Point
// ========================================
function startDownload() {
    if (!currentVideoUrl) return;
    
    hideError();
    hideSuccess();
    
    // Show modal to choose download method
    showDownloadModal();
}

// ========================================
// DOWNLOAD - Execute
// ========================================
async function executeDownload(useFolder) {
    showProgress();
    updateProgress(0);
    
    // Determine format_id to use
    const formatId = selectedFormat === "mp3" 
        ? "mp3" 
        : (selectedFormatId || "best");
    
    const downloadUrl = `${API}/download?url=${encodeURIComponent(currentVideoUrl)}&format_id=${encodeURIComponent(formatId)}`;
    
    // Generate filename early
    const ext = selectedFormat === "mp3" ? ".mp3" : ".mp4";
    const safeName = (currentVideoData?.title || "video").replace(/[^a-zA-Z0-9\s]/g, "").trim().substring(0, 50) || "video";
    const fallbackFileName = safeName + ext;
    
    try {
        if (useFolder && pendingDownloadFolder) {
            // Streaming download to folder
            await downloadToFolderStreaming(downloadUrl, fallbackFileName);
        } else {
            // Normal browser download - instant, no waiting
            triggerBrowserDownload(downloadUrl, fallbackFileName);
        }
    } catch (err) {
        console.error("Download error:", err);
        hideProgress();
        
        // If folder download failed, offer fallback
        if (useFolder) {
            showError("Folder save failed. Try 'Download Normally' instead.", "");
        } else {
            showError("Download failed", err.message || "Please try again");
        }
    }
}

// ========================================
// INSTANT BROWSER DOWNLOAD
// ========================================
function triggerBrowserDownload(url, fallbackName) {
    // Create invisible link and click it - instant download start
    const a = document.createElement("a");
    a.href = url;
    a.download = fallbackName;
    a.style.display = "none";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    
    // Show success after a short delay (download has started)
    updateProgress(100);
    setTimeout(() => {
        hideProgress();
        showSuccess();
        saveToHistory(currentVideoData?.title || currentVideoUrl);
    }, 500);
}

// ========================================
// STREAMING DOWNLOAD TO FOLDER
// ========================================
async function downloadToFolderStreaming(url, fallbackFileName) {
    const response = await fetch(url);
    
    // Check for error response (JSON)
    const contentType = response.headers.get("content-type") || "";
    if (contentType.includes("application/json")) {
        const data = await response.json();
        hideProgress();
        showError(data.message || data.error || "Download failed", data.hint || "");
        return;
    }
    
    if (!response.ok) {
        throw new Error(`Server error: ${response.status}`);
    }
    
    // Get filename from header or use fallback
    const fileName = getFileNameFromResponse(response) || fallbackFileName;
    
    // Get content length for progress
    const contentLength = response.headers.get("content-length");
    const totalSize = contentLength ? parseInt(contentLength) : null;
    
    try {
        // Verify folder permission
        const permission = await pendingDownloadFolder.queryPermission({ mode: "readwrite" });
        if (permission !== "granted") {
            const result = await pendingDownloadFolder.requestPermission({ mode: "readwrite" });
            if (result !== "granted") {
                throw new Error("Folder permission denied");
            }
        }
        
        // Create file and get writable stream
        const fileHandle = await pendingDownloadFolder.getFileHandle(fileName, { create: true });
        const writable = await fileHandle.createWritable();
        
        // Stream the response
        const reader = response.body.getReader();
        let receivedBytes = 0;
        
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            
            await writable.write(value);
            receivedBytes += value.length;
            
            // Update progress
            if (totalSize) {
                const percent = (receivedBytes / totalSize) * 100;
                updateProgress(Math.min(percent, 99));
            } else {
                // Estimate progress without content-length
                updateProgress(Math.min(50 + (receivedBytes / 10000000) * 40, 95));
            }
        }
        
        await writable.close();
        
        // Success
        updateProgress(100);
        setTimeout(() => {
            hideProgress();
            showSuccess();
            saveToHistory(currentVideoData?.title || currentVideoUrl);
        }, 300);
        
    } catch (err) {
        console.error("Folder streaming error:", err);
        throw err;
    }
}

function getFileNameFromResponse(response) {
    const contentDisposition = response.headers.get("content-disposition");
    if (contentDisposition) {
        const match = contentDisposition.match(/filename="?([^";\n]+)"?/);
        if (match) return match[1].trim();
    }
    return null;
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
    hideDownloadModal();
    videoPreview.classList.add("hidden");
    qualitySection.classList.add("hidden");
    downloadSection.classList.add("hidden");
    currentVideoData = null;
    qualityToFormatMap = {};
    selectedQuality = null;
    selectedFormatId = null;
    pendingDownloadFolder = null;
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
