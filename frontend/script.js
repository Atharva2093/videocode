/* ========================================
   YOUTUBE DOWNLOADER - STRICT FOLDER MODE
   ========================================
   ENFORCES:
   - File System Access API only (Chrome/Edge)
   - NO fallback auto-downloads
   - NO anchor-based downloads
   - NO window.location redirects
   - Folder picker EVERY time
   - Streaming write to selected folder
======================================== */

"use strict";

// ========================================
// API DETECTION (local / prod)
// ========================================
const API =
  window.location.hostname === "localhost" ||
  window.location.hostname === "127.0.0.1"
    ? "http://127.0.0.1:8000/api"
    : "https://yt-downloader-backend-ogpx.onrender.com/api";

// ========================================
// GLOBALS
// ========================================
let selectedFormat = "mp4";
let selectedQuality = "720p";
let selectedFormatId = null;
let currentVideoUrl = "";
let currentTitle = "";

// ========================================
// DOM ELEMENTS
// ========================================
const urlInput = document.getElementById("url");
const infoDiv = document.getElementById("info");
const loading = document.getElementById("loading");
const qualitySelector = document.getElementById("qualitySelector");
const downloadBtn = document.getElementById("downloadBtn");
const progressContainer = document.getElementById("progressContainer");
const progressBar = document.getElementById("progressBar");
const progressPercent = document.getElementById("progressPercent");
const errorBox = document.getElementById("errorBox");
const errorMessage = document.getElementById("errorMessage");
const errorHint = document.getElementById("errorHint");
const successBox = document.getElementById("successBox");
const folderModal = document.getElementById("folderModal");
const historyDiv = document.getElementById("history");
const connectionStatus = document.getElementById("connectionStatus");

// ========================================
// BROWSER SUPPORT CHECK
// ========================================
function isFolderPickerSupported() {
  return typeof window.showDirectoryPicker === "function";
}

// ========================================
// THEME TOGGLE
// ========================================
function toggleTheme() {
  const html = document.documentElement;
  const newTheme = html.dataset.theme === "dark" ? "light" : "dark";
  html.dataset.theme = newTheme;
  
  const btn = document.querySelector(".theme-toggle");
  if (btn) btn.textContent = newTheme === "dark" ? "🌙" : "☀️";
  
  localStorage.setItem("theme", newTheme);
}

// Load saved theme on page load
(function loadTheme() {
  const saved = localStorage.getItem("theme");
  if (saved) {
    document.documentElement.dataset.theme = saved;
    const btn = document.querySelector(".theme-toggle");
    if (btn) btn.textContent = saved === "dark" ? "🌙" : "☀️";
  }
})();

// ========================================
// ERROR / SUCCESS DISPLAY
// ========================================
function showError(msg, hint = "") {
  errorBox.classList.remove("hidden");
  errorMessage.textContent = msg;
  if (errorHint) errorHint.textContent = hint;
  successBox.classList.add("hidden");
  progressContainer.classList.add("hidden");
}

function hideError() {
  errorBox.classList.add("hidden");
  errorMessage.textContent = "";
  if (errorHint) errorHint.textContent = "";
}

function showSuccess() {
  successBox.classList.remove("hidden");
  setTimeout(() => successBox.classList.add("hidden"), 5000);
}

function hideSuccess() {
  successBox.classList.add("hidden");
}

// ========================================
// FORMAT TOGGLE (MP4 / MP3)
// ========================================
function setFormat(f) {
  selectedFormat = f;
  document.getElementById("btnMp4").classList.toggle("active", f === "mp4");
  document.getElementById("btnMp3").classList.toggle("active", f === "mp3");
  
  // Hide quality selector for MP3
  if (f === "mp3") {
    qualitySelector.classList.add("hidden");
  } else if (infoDiv.innerHTML) {
    qualitySelector.classList.remove("hidden");
  }
}

// ========================================
// FETCH VIDEO METADATA
// ========================================
async function getInfo() {
  hideError();
  hideSuccess();
  infoDiv.innerHTML = "";
  qualitySelector.classList.add("hidden");
  downloadBtn.classList.add("hidden");
  loading.classList.remove("hidden");
  
  const url = urlInput.value.trim();
  if (!url) {
    loading.classList.add("hidden");
    showError("Please enter a YouTube URL.");
    return;
  }
  
  try {
    const res = await fetch(`${API}/metadata?url=${encodeURIComponent(url)}`);
    const data = await res.json();
    loading.classList.add("hidden");
    
    if (data.error) {
      showError(data.message || "Failed to fetch video info.", data.hint || "");
      return;
    }
    
    currentVideoUrl = url;
    currentTitle = data.title || "video";
    
    // Build video info UI
    const duration = data.duration 
      ? `${Math.floor(data.duration / 60)}m ${data.duration % 60}s`
      : "";
    
    infoDiv.innerHTML = `
      <div class="video-card">
        <img src="${data.thumbnail || ''}" alt="Thumbnail">
        <div>
          <p class="video-title">${escapeHtml(data.title || "Unknown")}</p>
          <p class="video-meta">${escapeHtml(data.channel || "")} ${duration ? "• " + duration : ""}</p>
        </div>
      </div>
    `;
    
    // Render quality chips
    const formats = data.video_formats || data.formats || [];
    renderQualityChips(formats);
    
    downloadBtn.classList.remove("hidden");
    
  } catch (err) {
    loading.classList.add("hidden");
    showError("Could not connect to server.", "Check if backend is running.");
    console.error("Metadata fetch error:", err);
  }
}

// ========================================
// QUALITY CHIPS
// ========================================
function renderQualityChips(formats) {
  // Build map: height -> best format for that height
  const seen = new Map();
  
  formats.forEach(f => {
    if (!f || !f.height) return;
    
    const key = f.height + "p";
    const existing = seen.get(key);
    
    // Prefer formats with audio
    if (!existing || (f.has_audio && !existing.has_audio)) {
      seen.set(key, {
        format_id: f.format_id || f.id,
        has_audio: f.has_audio,
        height: f.height
      });
    }
  });
  
  const heights = Array.from(seen.keys()).sort((a, b) => parseInt(b) - parseInt(a));
  
  if (heights.length === 0) {
    qualitySelector.innerHTML = `<button class="quality-chip active" data-format-id="best">Best Available</button>`;
    qualitySelector.classList.remove("hidden");
    selectedFormatId = "best";
    return;
  }
  
  // Default to 720p if available, else highest
  const defaultQuality = heights.includes("720p") ? "720p" : heights[0];
  selectedQuality = defaultQuality;
  selectedFormatId = seen.get(defaultQuality)?.format_id || "best";
  
  qualitySelector.innerHTML = heights.map(h => {
    const entry = seen.get(h);
    const isActive = h === defaultQuality;
    return `
      <button 
        class="quality-chip ${isActive ? 'active' : ''}" 
        data-format-id="${entry.format_id}"
        data-quality="${h}"
        onclick="onSelectQuality(this)"
      >
        ${h}
      </button>
    `;
  }).join("");
  
  qualitySelector.classList.remove("hidden");
}

// Called when clicking a quality chip
function onSelectQuality(el) {
  document.querySelectorAll(".quality-chip").forEach(c => c.classList.remove("active"));
  el.classList.add("active");
  selectedQuality = el.dataset.quality;
  selectedFormatId = el.dataset.formatId;
}

// ========================================
// DOWNLOAD BUTTON -> CHECK SUPPORT & SHOW MODAL
// ========================================
function onDownloadClick() {
  hideError();
  hideSuccess();
  
  // STRICT: Check browser support FIRST
  if (!isFolderPickerSupported()) {
    showError(
      "Your browser does not support folder saving.",
      "Please use Google Chrome or Microsoft Edge to download videos."
    );
    return; // DO NOT proceed, NO fallback
  }
  
  // Show folder selection modal
  folderModal.classList.remove("hidden");
  folderModal.setAttribute("aria-hidden", "false");
}

// ========================================
// MODAL FUNCTIONS
// ========================================
function closeFolderModal() {
  folderModal.classList.add("hidden");
  folderModal.setAttribute("aria-hidden", "true");
}

// ========================================
// FOLDER SELECTION & STREAMING DOWNLOAD
// ========================================
async function chooseFolderAndStart() {
  closeFolderModal();
  
  // Double-check support (defensive)
  if (!isFolderPickerSupported()) {
    showError(
      "Your browser does not support folder saving.",
      "Please use Google Chrome or Microsoft Edge."
    );
    return;
  }
  
  // ALWAYS prompt for folder - never reuse old permissions
  let folder;
  try {
    folder = await window.showDirectoryPicker({ mode: "readwrite" });
  } catch (err) {
    // User cancelled the picker
    console.log("Folder selection cancelled:", err.name, err.message);
    return; // Do nothing, no fallback
  }
  
  // Folder selected - start streaming download
  await streamDownloadToFolder(folder);
}

// ========================================
// GET SELECTED FORMAT ID
// ========================================
function getSelectedFormatId() {
  if (selectedFormat === "mp3") return "mp3";
  if (selectedFormatId) return selectedFormatId;
  
  // Fallback: check active chip
  const activeChip = document.querySelector(".quality-chip.active");
  if (activeChip?.dataset.formatId) return activeChip.dataset.formatId;
  
  return "best";
}

// ========================================
// STREAM DOWNLOAD TO FOLDER (CORE LOGIC)
// ========================================
async function streamDownloadToFolder(folder) {
  hideError();
  hideSuccess();
  
  // Show progress
  progressContainer.classList.remove("hidden");
  progressBar.style.width = "0%";
  progressPercent.textContent = "Connecting...";
  
  const formatId = getSelectedFormatId();
  const downloadUrl = `${API}/download?url=${encodeURIComponent(currentVideoUrl)}&format_id=${encodeURIComponent(formatId)}`;
  
  console.log("[Download] Starting:", downloadUrl);
  
  // ========================================
  // STEP 1: Fetch the download stream
  // ========================================
  let response;
  try {
    response = await fetch(downloadUrl);
    console.log("[Download] Response status:", response.status);
  } catch (networkErr) {
    console.error("[Download] Network error:", networkErr);
    progressContainer.classList.add("hidden");
    showError("Network error: Could not reach server.", "Check your internet connection.");
    return;
  }
  
  // ========================================
  // STEP 2: Check for error responses
  // ========================================
  const contentType = response.headers.get("Content-Type") || "";
  console.log("[Download] Content-Type:", contentType);
  
  if (contentType.includes("application/json")) {
    // Server returned an error as JSON
    let errData = {};
    try {
      errData = await response.json();
    } catch (e) {
      errData = { message: "Unknown error" };
    }
    console.error("[Download] Server error:", errData);
    progressContainer.classList.add("hidden");
    showError(errData.message || "Download failed.", errData.hint || "");
    return;
  }
  
  if (!response.ok) {
    console.error("[Download] HTTP error:", response.status);
    progressContainer.classList.add("hidden");
    showError(`Server error: ${response.status} ${response.statusText}`, "Try again later.");
    return;
  }
  
  // ========================================
  // STEP 3: Verify response body exists
  // ========================================
  if (!response.body) {
    console.error("[Download] No response body");
    progressContainer.classList.add("hidden");
    showError("Download failed.", "Server did not return file data.");
    return;
  }
  
  // ========================================
  // STEP 4: Extract filename
  // ========================================
  const disposition = response.headers.get("Content-Disposition");
  console.log("[Download] Content-Disposition:", disposition);
  
  let filename = extractFilename(disposition);
  if (!filename) {
    // Generate fallback filename
    const ext = selectedFormat === "mp3" ? ".mp3" : ".mp4";
    const timestamp = Date.now();
    const safeName = sanitizeFilename(currentTitle) || "video";
    filename = `${safeName}_${timestamp}${ext}`;
  }
  console.log("[Download] Filename:", filename);
  
  // ========================================
  // STEP 5: Get content length for progress
  // ========================================
  const contentLengthHeader = response.headers.get("Content-Length");
  const totalBytes = contentLengthHeader ? parseInt(contentLengthHeader, 10) : 0;
  console.log("[Download] Total bytes:", totalBytes);
  
  // ========================================
  // STEP 6: Create file in selected folder
  // ========================================
  let fileHandle;
  try {
    fileHandle = await folder.getFileHandle(filename, { create: true });
    console.log("[Download] File handle created");
  } catch (err) {
    console.error("[Download] getFileHandle error:", err);
    progressContainer.classList.add("hidden");
    showError("Could not create file.", "Check folder permissions and try again.");
    return;
  }
  
  // ========================================
  // STEP 7: Open writable stream
  // ========================================
  let writable;
  try {
    writable = await fileHandle.createWritable();
    console.log("[Download] Writable stream opened");
  } catch (err) {
    console.error("[Download] createWritable error:", err);
    progressContainer.classList.add("hidden");
    showError("Could not open file for writing.", "The file may be locked or folder is read-only.");
    return;
  }
  
  // ========================================
  // STEP 8: Stream and write chunks
  // ========================================
  progressPercent.textContent = "Downloading...";
  
  let reader;
  try {
    reader = response.body.getReader();
  } catch (err) {
    console.error("[Download] getReader error:", err);
    try { await writable.abort(); } catch (e) {}
    progressContainer.classList.add("hidden");
    showError("Could not read download stream.", "Please try again.");
    return;
  }
  
  let receivedBytes = 0;
  let lastProgressUpdate = 0;
  
  try {
    while (true) {
      const readResult = await reader.read();
      
      if (readResult.done) {
        console.log("[Download] Stream complete, total:", receivedBytes);
        break;
      }
      
      const chunk = readResult.value;
      if (!chunk || chunk.length === 0) {
        continue; // Skip empty chunks
      }
      
      // Write chunk to file
      await writable.write(chunk);
      receivedBytes += chunk.length;
      
      // Throttle progress updates (every 100ms)
      const now = Date.now();
      if (now - lastProgressUpdate > 100) {
        lastProgressUpdate = now;
        
        if (totalBytes > 0) {
          const percent = Math.min(99, Math.round((receivedBytes / totalBytes) * 100));
          progressBar.style.width = percent + "%";
          progressPercent.textContent = `${percent}%`;
        } else {
          const mb = (receivedBytes / (1024 * 1024)).toFixed(1);
          progressBar.style.width = "60%";
          progressPercent.textContent = `${mb} MB`;
        }
      }
    }
    
    // ========================================
    // STEP 9: Finalize file
    // ========================================
    await writable.close();
    console.log("[Download] File saved successfully");
    
    // Success UI
    progressBar.style.width = "100%";
    progressPercent.textContent = "100% - Complete!";
    
    saveToHistory(currentTitle, filename);
    showSuccess();
    
    // Hide progress after delay
    setTimeout(() => {
      progressContainer.classList.add("hidden");
      progressBar.style.width = "0%";
      progressPercent.textContent = "0%";
    }, 2500);
    
  } catch (streamErr) {
    console.error("[Download] Streaming error:", streamErr);
    
    // Try to abort the writable stream
    try {
      await writable.abort();
      console.log("[Download] Writable aborted");
    } catch (abortErr) {
      console.error("[Download] Abort error:", abortErr);
    }
    
    // Try to cancel the reader
    try {
      await reader.cancel();
      console.log("[Download] Reader cancelled");
    } catch (cancelErr) {
      console.error("[Download] Cancel error:", cancelErr);
    }
    
    progressContainer.classList.add("hidden");
    showError("Download failed during file write.", "Check disk space and folder permissions.");
  }
}

// ========================================
// EXTRACT FILENAME FROM CONTENT-DISPOSITION
// ========================================
function extractFilename(header) {
  if (!header) return null;
  
  try {
    // Try filename*= (RFC 5987 encoded) first
    let match = /filename\*\s*=\s*(?:UTF-8''|utf-8'')?([^;\r\n]+)/i.exec(header);
    if (match && match[1]) {
      const decoded = decodeURIComponent(match[1].replace(/['"]/g, "").trim());
      if (decoded) return decoded;
    }
    
    // Try filename= with quotes
    match = /filename\s*=\s*"([^"]+)"/i.exec(header);
    if (match && match[1]) {
      return match[1].trim();
    }
    
    // Try filename= without quotes
    match = /filename\s*=\s*([^;\s]+)/i.exec(header);
    if (match && match[1]) {
      return match[1].replace(/['"]/g, "").trim();
    }
  } catch (e) {
    console.warn("[Download] Filename extraction error:", e);
  }
  
  return null;
}

// ========================================
// SANITIZE FILENAME
// ========================================
function sanitizeFilename(name) {
  if (!name) return "video";
  
  return name
    .replace(/[<>:"/\\|?*\x00-\x1F]/g, "") // Remove illegal chars
    .replace(/\s+/g, " ")                   // Collapse whitespace
    .trim()
    .substring(0, 120);                     // Limit length
}

// ========================================
// ESCAPE HTML
// ========================================
function escapeHtml(text) {
  if (!text) return "";
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

// ========================================
// HISTORY (localStorage)
// ========================================
function saveToHistory(title, filename) {
  const history = JSON.parse(localStorage.getItem("downloadHistory") || "[]");
  
  history.unshift({
    name: (title || "Unknown").substring(0, 80),
    file: filename || "",
    time: new Date().toLocaleString()
  });
  
  // Keep only last 10 items
  while (history.length > 10) {
    history.pop();
  }
  
  localStorage.setItem("downloadHistory", JSON.stringify(history));
  renderHistory();
}

function renderHistory() {
  const arr = JSON.parse(localStorage.getItem("downloadHistory") || "[]");
  
  if (arr.length === 0) {
    historyDiv.innerHTML = '<div class="history-item">No downloads yet</div>';
    return;
  }
  
  historyDiv.innerHTML = arr.map(h => `
    <div class="history-item">
      <strong>${escapeHtml(h.name)}</strong>
      <small>${h.file ? escapeHtml(h.file) + " • " : ""}${h.time}</small>
    </div>
  `).join("");
}

// Render history on load
renderHistory();

// ========================================
// CONNECTION STATUS CHECK
// ========================================
async function checkConnection() {
  try {
    const res = await fetch(`${API}/health`, { method: "GET" });
    const data = await res.json();
    
    if (data.status === "ok") {
      connectionStatus.textContent = "● Connected";
      connectionStatus.classList.remove("offline");
      connectionStatus.classList.add("online");
    } else {
      throw new Error("Not ok");
    }
  } catch (err) {
    connectionStatus.textContent = "● Offline";
    connectionStatus.classList.remove("online");
    connectionStatus.classList.add("offline");
  }
}

// Check connection on load and periodically
checkConnection();
setInterval(checkConnection, 30000);

// ========================================
// EVENT LISTENERS
// ========================================
urlInput.addEventListener("keypress", (e) => {
  if (e.key === "Enter") getInfo();
});

// Close modal when clicking outside
folderModal.addEventListener("click", (e) => {
  if (e.target === folderModal) {
    closeFolderModal();
  }
});

// Escape key closes modal
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape" && !folderModal.classList.contains("hidden")) {
    closeFolderModal();
  }
});

// ========================================
// EXPOSE FUNCTIONS TO HTML onclick
// ========================================
window.toggleTheme = toggleTheme;
window.setFormat = setFormat;
window.getInfo = getInfo;
window.onSelectQuality = onSelectQuality;
window.onDownloadClick = onDownloadClick;
window.chooseFolderAndStart = chooseFolderAndStart;
window.closeFolderModal = closeFolderModal;

// ========================================
// REMOVED FUNCTIONS (for clarity)
// ========================================
// The following have been intentionally removed:
// - downloadNormallyFromModal() - NO fallback downloads
// - Any code using window.location.href
// - Any code using <a download> anchors
// - Any code using a.click()
// - Any localStorage caching of folder permissions
