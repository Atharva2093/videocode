/* ========================================
   YOUTUBE DOWNLOADER - FRONTEND SCRIPT
   Enforces folder selection before download
   Works only in Chrome/Edge (File System Access API)
======================================== */

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
let currentFilename = "";

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
// THEME TOGGLE
// ========================================
function toggleTheme() {
  const html = document.documentElement;
  const newTheme = html.dataset.theme === "dark" ? "light" : "dark";
  html.dataset.theme = newTheme;
  
  const btn = document.querySelector(".theme-toggle");
  btn.textContent = newTheme === "dark" ? "🌙" : "☀️";
  
  localStorage.setItem("theme", newTheme);
}

// Load saved theme
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
}

function hideError() {
  errorBox.classList.add("hidden");
  errorMessage.textContent = "";
  if (errorHint) errorHint.textContent = "";
}

function showSuccess() {
  successBox.classList.remove("hidden");
  setTimeout(() => successBox.classList.add("hidden"), 4000);
}

function hideSuccess() {
  successBox.classList.add("hidden");
}

// ========================================
// FORMAT TOGGLE
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
    console.error(err);
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
// DOWNLOAD BUTTON CLICKED -> SHOW MODAL
// ========================================
function onDownloadClick() {
  hideError();
  hideSuccess();
  
  // Always show modal to choose download method
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

// "Download Normally" - Opens browser Save dialog
function downloadNormallyFromModal() {
  closeFolderModal();
  
  const formatId = getSelectedFormatId();
  const downloadUrl = `${API}/download?url=${encodeURIComponent(currentVideoUrl)}&format_id=${encodeURIComponent(formatId)}`;
  
  // Create temporary anchor - browser will show Save dialog
  const a = document.createElement("a");
  a.href = downloadUrl;
  a.download = sanitizeFilename(currentTitle) + (selectedFormat === "mp3" ? ".mp3" : ".mp4");
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  
  // Record history
  saveToHistory(currentTitle);
  showSuccess();
}

// "Select Folder & Save" - Use File System Access API
async function chooseFolderAndStart() {
  closeFolderModal();
  
  // Check browser support
  if (!window.showDirectoryPicker) {
    showError(
      "Folder selection not supported in this browser.",
      "Use Chrome or Edge, or click 'Download Normally'."
    );
    return;
  }
  
  let folder;
  try {
    // FORCE folder selection every time (no caching)
    folder = await window.showDirectoryPicker();
  } catch (err) {
    console.log("Folder selection cancelled:", err);
    // User cancelled - do nothing
    return;
  }
  
  // Start streaming download to selected folder
  await downloadToFolder(folder);
}

// ========================================
// GET SELECTED FORMAT ID
// ========================================
function getSelectedFormatId() {
  if (selectedFormat === "mp3") return "mp3";
  if (selectedFormatId) return selectedFormatId;
  
  // Fallback
  const activeChip = document.querySelector(".quality-chip.active");
  if (activeChip?.dataset.formatId) return activeChip.dataset.formatId;
  
  return "best";
}

// ========================================
// STREAM DOWNLOAD TO FOLDER
// ========================================
async function downloadToFolder(folder) {
  hideError();
  hideSuccess();
  progressContainer.classList.remove("hidden");
  progressBar.style.width = "0%";
  progressPercent.textContent = "0%";
  
  const formatId = getSelectedFormatId();
  const downloadUrl = `${API}/download?url=${encodeURIComponent(currentVideoUrl)}&format_id=${encodeURIComponent(formatId)}`;
  
  try {
    const response = await fetch(downloadUrl);
    
    // Check for error response
    if (!response.ok) {
      const errJson = await response.json().catch(() => null);
      progressContainer.classList.add("hidden");
      showError(errJson?.message || `Download failed: ${response.status}`, errJson?.hint || "");
      return;
    }
    
    // Get filename from Content-Disposition header or use fallback
    let filename = getFilenameFromResponse(response);
    if (!filename) {
      const ext = selectedFormat === "mp3" ? ".mp3" : ".mp4";
      filename = sanitizeFilename(currentTitle) + ext;
    }
    currentFilename = filename;
    
    // Get content length for progress calculation
    const contentLength = parseInt(response.headers.get("Content-Length") || "0", 10);
    
    // Create file in selected folder
    const fileHandle = await folder.getFileHandle(filename, { create: true });
    const writable = await fileHandle.createWritable();
    
    // Stream response body and write chunks
    const reader = response.body.getReader();
    let receivedBytes = 0;
    
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      
      // Write chunk to file
      await writable.write(value);
      receivedBytes += value.length;
      
      // Update progress
      if (contentLength > 0) {
        const percent = Math.min(100, Math.round((receivedBytes / contentLength) * 100));
        progressBar.style.width = percent + "%";
        progressPercent.textContent = percent + "%";
      } else {
        // Approximate progress when Content-Length not available
        const approxPercent = Math.min(95, Math.round(receivedBytes / 1000000) * 5);
        progressBar.style.width = approxPercent + "%";
        progressPercent.textContent = approxPercent + "%";
      }
    }
    
    // Finalize file
    await writable.close();
    
    // Success!
    progressBar.style.width = "100%";
    progressPercent.textContent = "100%";
    
    saveToHistory(currentTitle + " → " + filename);
    showSuccess();
    
    // Hide progress after a moment
    setTimeout(() => {
      progressContainer.classList.add("hidden");
      progressBar.style.width = "0%";
      progressPercent.textContent = "0%";
    }, 1500);
    
  } catch (err) {
    console.error("Download error:", err);
    progressContainer.classList.add("hidden");
    showError("Download failed during streaming.", "Check folder permission and try again.");
  }
}

// ========================================
// HELPER FUNCTIONS
// ========================================
function sanitizeFilename(name) {
  return (name || "video")
    .replace(/[<>:"/\\|?*\x00-\x1F]/g, "")
    .replace(/\s+/g, " ")
    .trim()
    .substring(0, 100);
}

function getFilenameFromResponse(response) {
  const cd = response.headers.get("Content-Disposition");
  if (!cd) return null;
  
  // Try filename*= (RFC 5987)
  let match = /filename\*=(?:UTF-8'')?["']?([^"';\n]+)["']?/i.exec(cd);
  if (match?.[1]) return decodeURIComponent(match[1]);
  
  // Try filename=
  match = /filename=["']?([^"';\n]+)["']?/i.exec(cd);
  if (match?.[1]) return match[1].trim();
  
  return null;
}

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

// ========================================
// HISTORY (localStorage)
// ========================================
function saveToHistory(name) {
  const history = JSON.parse(localStorage.getItem("downloadHistory") || "[]");
  
  history.unshift({
    name: name.substring(0, 80),
    time: new Date().toLocaleString(),
    file: currentFilename || ""
  });
  
  // Keep only last 8 items
  if (history.length > 8) history.pop();
  
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
      ${escapeHtml(h.name)}
      <small>${h.time}${h.file ? " • " + escapeHtml(h.file) : ""}</small>
    </div>
  `).join("");
}

// Initial render
renderHistory();

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

// Check connection on load and every 30 seconds
checkConnection();
setInterval(checkConnection, 30000);

// ========================================
// EVENT LISTENERS
// ========================================
urlInput.addEventListener("keypress", (e) => {
  if (e.key === "Enter") getInfo();
});

// Close modal on overlay click
folderModal.addEventListener("click", (e) => {
  if (e.target === folderModal) closeFolderModal();
});

// ========================================
// EXPOSE FUNCTIONS TO HTML
// ========================================
window.toggleTheme = toggleTheme;
window.setFormat = setFormat;
window.getInfo = getInfo;
window.onSelectQuality = onSelectQuality;
window.onDownloadClick = onDownloadClick;
window.chooseFolderAndStart = chooseFolderAndStart;
window.downloadNormallyFromModal = downloadNormallyFromModal;
window.closeFolderModal = closeFolderModal;
