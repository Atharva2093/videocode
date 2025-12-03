"use strict";

const API = (location.hostname === "localhost" || location.hostname === "127.0.0.1")
  ? "http://127.0.0.1:8000/api"
  : "https://yt-downloader-backend-ogpx.onrender.com/api";

let currentUrl = "";
let currentTitle = "";
let currentMetadata = null;
let selectedFormatId = null;

const $ = id => document.getElementById(id);
const urlInput = $("url");
const infoDiv = $("info");
const loading = $("loading");
const qualitySelector = $("qualitySelector");
const downloadBtn = $("downloadBtn");
const progressContainer = $("progressContainer");
const progressBar = $("progressBar");
const progressPercent = $("progressPercent");
const errorBox = $("errorBox");
const errorMessage = $("errorMessage");
const errorHint = $("errorHint");
const successBox = $("successBox");
const folderModal = $("folderModal");
const historyDiv = $("history");
const connectionStatus = $("connectionStatus");
const toastContainer = $("toastContainer");
const floatingProgress = $("floatingProgress");
const floatingProgressText = $("floatingProgressText");

document.addEventListener("DOMContentLoaded", () => {
  loadTheme();
  renderHistory();
  checkConnection();
  setInterval(checkConnection, 30000);
  
  urlInput.addEventListener("keypress", e => { if (e.key === "Enter") getInfo(); });
  urlInput.addEventListener("input", hideError);
  folderModal.addEventListener("click", e => { if (e.target === folderModal) closeFolderModal(); });
  document.addEventListener("keydown", e => { if (e.key === "Escape") closeFolderModal(); });
});

function loadTheme() {
  const theme = localStorage.getItem("theme") || "dark";
  document.documentElement.dataset.theme = theme;
  const btn = document.querySelector(".theme-toggle");
  if (btn) btn.textContent = theme === "dark" ? "🌙" : "☀️";
}

function toggleTheme() {
  const next = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
  document.documentElement.dataset.theme = next;
  localStorage.setItem("theme", next);
  const btn = document.querySelector(".theme-toggle");
  if (btn) btn.textContent = next === "dark" ? "🌙" : "☀️";
}

function isValidUrl(url) {
  if (!url) return false;
  const patterns = [
    /^(https?:\/\/)?(www\.)?youtube\.com\/watch\?v=[\w-]{11}/,
    /^(https?:\/\/)?(www\.)?youtu\.be\/[\w-]{11}/,
    /^(https?:\/\/)?(www\.)?youtube\.com\/shorts\/[\w-]{11}/,
    /^(https?:\/\/)?(www\.)?youtube\.com\/embed\/[\w-]{11}/
  ];
  return patterns.some(p => p.test(url.trim()));
}

function showError(msg, hint = "") {
  errorBox.classList.remove("hidden");
  errorMessage.textContent = msg;
  errorHint.textContent = hint;
  successBox.classList.add("hidden");
}

function hideError() { errorBox.classList.add("hidden"); }

function showSuccess() {
  successBox.classList.remove("hidden");
  setTimeout(() => successBox.classList.add("hidden"), 4000);
}

function showToast(msg, type = "info", duration = 3000) {
  const t = document.createElement("div");
  t.className = `toast ${type}`;
  t.innerHTML = `<span>${type === "success" ? "✅" : type === "error" ? "❌" : "⬇️"}</span><span>${msg}</span>`;
  toastContainer.appendChild(t);
  setTimeout(() => t.remove(), duration);
}

async function checkConnection() {
  try {
    const res = await fetch(`${API}/health`);
    const data = await res.json();
    if (data.status === "ok") {
      connectionStatus.textContent = "● Connected";
      connectionStatus.className = "status-badge online";
    } else throw new Error();
  } catch {
    connectionStatus.textContent = "● Offline";
    connectionStatus.className = "status-badge offline";
  }
}

async function getInfo() {
  hideError();
  successBox.classList.add("hidden");
  infoDiv.innerHTML = "";
  qualitySelector.classList.add("hidden");
  downloadBtn.classList.add("hidden");
  
  const url = urlInput.value.trim();
  if (!url) return showError("Please enter a YouTube URL.");
  if (!isValidUrl(url)) return showError("Invalid YouTube URL.", "Check the format and try again.");
  
  loading.classList.remove("hidden");
  
  let data = null;
  for (let i = 0; i < 2; i++) {
    try {
      const res = await fetch(`${API}/metadata?url=${encodeURIComponent(url)}`);
      data = await res.json();
      if (data.error) throw new Error(data.message || "Failed to fetch info");
      break;
    } catch (err) {
      if (i === 1) {
        loading.classList.add("hidden");
        return showError(err.message || "Could not fetch video info.", "Check connection or try again.");
      }
      await new Promise(r => setTimeout(r, 1000));
    }
  }
  
  loading.classList.add("hidden");
  
  if (!data?.title) return showError("Could not load video.", "Try a different video.");
  
  currentUrl = url;
  currentTitle = data.title;
  currentMetadata = data;
  
  const dur = data.duration ? `${Math.floor(data.duration/60)}:${String(data.duration%60).padStart(2,"0")}` : "";
  
  infoDiv.innerHTML = `
    <div class="video-card">
      <img src="${data.thumbnail||""}" alt="" onerror="this.style.display='none'">
      <div class="video-info">
        <p class="video-title">${escapeHtml(data.title)}</p>
        <p class="video-meta">${escapeHtml(data.channel||"")}${dur?" • "+dur:""}</p>
      </div>
    </div>`;
  
  renderQualityChips(data.video_formats || []);
  downloadBtn.classList.remove("hidden");
}

function renderQualityChips(formats) {
  const map = new Map();
  formats.forEach(f => {
    if (!f?.height) return;
    const key = f.height + "p";
    const existing = map.get(key);
    if (!existing || (f.has_audio && !existing.has_audio)) {
      map.set(key, { format_id: f.format_id, has_audio: f.has_audio });
    }
  });
  
  const qualities = [...map.keys()].sort((a,b) => parseInt(b) - parseInt(a));
  
  if (!qualities.length) {
    qualitySelector.innerHTML = `<button class="quality-chip active" data-format-id="best">Best</button>`;
    selectedFormatId = "best";
  } else {
    const def = qualities.includes("720p") ? "720p" : qualities[0];
    selectedFormatId = map.get(def)?.format_id || "best";
    qualitySelector.innerHTML = qualities.map(q => 
      `<button class="quality-chip ${q===def?"active":""}" data-format-id="${map.get(q).format_id}" onclick="selectQuality(this)">${q}</button>`
    ).join("");
  }
  qualitySelector.classList.remove("hidden");
}

function selectQuality(el) {
  document.querySelectorAll(".quality-chip").forEach(c => c.classList.remove("active"));
  el.classList.add("active");
  selectedFormatId = el.dataset.formatId;
}

function onDownloadClick() {
  hideError();
  if (!currentUrl) return showError("No video selected.", "Fetch a video first.");
  if (!currentMetadata) return showError("Metadata missing.", "Fetch the video again.");
  if (!selectedFormatId) return showError("No quality selected.");
  
  if (typeof window.showDirectoryPicker !== "function") {
    return showError("Browser not supported.", "Use Chrome or Edge.");
  }
  
  folderModal.classList.remove("hidden");
}

function closeFolderModal() { folderModal.classList.add("hidden"); }

async function chooseFolderAndStart() {
  closeFolderModal();
  
  let folder;
  try {
    folder = await window.showDirectoryPicker({ mode: "readwrite" });
  } catch { return; }
  
  await downloadToFolder(folder);
}

async function downloadToFolder(folder) {
  hideError();
  successBox.classList.add("hidden");
  resetProgress();
  
  showToast("Download started…", "info", 2500);
  setDownloadState("downloading");
  floatingProgress.classList.remove("hidden");
  progressContainer.classList.remove("hidden");
  
  let writable;
  let filename;
  
  try {
    const res = await fetch(`${API}/download?url=${encodeURIComponent(currentUrl)}&format_id=${encodeURIComponent(selectedFormatId)}`);
    
    const ct = res.headers.get("Content-Type") || "";
    if (ct.includes("application/json")) {
      const err = await res.json();
      throw new Error(err.message || "Download failed");
    }
    
    if (!res.ok) throw new Error(`Server error: ${res.status}`);
    if (!res.body) throw new Error("No data received");
    
    const disposition = res.headers.get("Content-Disposition") || "";
    filename = resolveFilename(disposition, currentTitle);
    const fileHandle = await folder.getFileHandle(filename, { create: true });
    writable = await fileHandle.createWritable();
    
    const total = parseInt(res.headers.get("Content-Length") || "0", 10);
    const reader = res.body.getReader();
    let received = 0;
    
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      await writable.write(value);
      received += value.length;
      
      if (total > 0) {
        const pct = Math.min(99, Math.round((received / total) * 100));
        updateProgress(pct);
      } else {
        const mb = (received / 1048576).toFixed(1);
        floatingProgressText.textContent = `${mb} MB`;
        progressPercent.textContent = `${mb} MB`;
      }
    }
    
    await writable.close();
    
    updateProgress(100);
    floatingProgress.classList.add("hidden");
    setDownloadState("completed");
    showToast("Download Completed!", "success", 4000);
    showSuccess();
    playSound();
    saveToHistory(currentTitle, filename);
    
    setTimeout(() => { setDownloadState("idle"); resetProgress(); }, 3000);
    
  } catch (err) {
    if (writable) {
      try { await writable.abort(); } catch (_) {}
    }
    floatingProgress.classList.add("hidden");
    setDownloadState("idle");
    progressContainer.classList.add("hidden");
    showError(err.message || "Download failed.", "Please try again.");
    showToast("Download failed", "error", 3000);
  }
}

function updateProgress(pct) {
  progressBar.style.width = pct + "%";
  progressPercent.textContent = pct + "%";
  floatingProgressText.textContent = pct + "%";
}

function resetProgress() {
  progressBar.style.width = "0%";
  progressPercent.textContent = "0%";
  progressContainer.classList.add("hidden");
}

function setDownloadState(state) {
  downloadBtn.classList.remove("downloading", "completed");
  if (state === "downloading") {
    downloadBtn.classList.add("downloading");
    downloadBtn.textContent = "⏳ Downloading...";
  } else if (state === "completed") {
    downloadBtn.classList.add("completed");
    downloadBtn.textContent = "✅ Downloaded!";
  } else {
    downloadBtn.textContent = "⬇️ Download MP4";
  }
}

function resolveFilename(disposition, fallbackTitle) {
  const fallback = sanitizeFilename(fallbackTitle) + ".mp4";
  if (!disposition) return fallback;
  const match = /filename="?([^";]+)"?/i.exec(disposition);
  if (!match) return fallback;
  const raw = match[1].trim();
  if (!raw) return fallback;
  const lastDot = raw.lastIndexOf(".");
  let base = raw;
  let ext = "mp4";
  if (lastDot > 0 && lastDot < raw.length - 1) {
    base = raw.slice(0, lastDot);
    ext = raw.slice(lastDot + 1);
  }
  const cleanBase = sanitizeFilename(base);
  const cleanExt = (ext || "mp4").replace(/[^a-zA-Z0-9]/g, "").toLowerCase();
  if (!cleanBase) return fallback;
  return `${cleanBase}.${cleanExt || "mp4"}`;
}

function sanitizeFilename(name) {
  if (!name) return "video";
  return name.replace(/[\\/:*?"<>|]/g, "").replace(/\s+/g, " ").trim().substring(0, 150) || "video";
}

function escapeHtml(text) {
  if (!text) return "";
  const d = document.createElement("div");
  d.textContent = text;
  return d.innerHTML;
}

function playSound() {
  try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.frequency.setValueAtTime(880, ctx.currentTime);
    osc.frequency.setValueAtTime(1100, ctx.currentTime + 0.1);
    gain.gain.setValueAtTime(0.15, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.2);
    osc.start(ctx.currentTime);
    osc.stop(ctx.currentTime + 0.2);
  } catch {}
}

function saveToHistory(title, filename) {
  const history = JSON.parse(localStorage.getItem("downloadHistory") || "[]");
  if (history.some(h => h.file === filename)) return;
  history.unshift({ name: title.substring(0, 80), file: filename, time: new Date().toLocaleString() });
  while (history.length > 10) history.pop();
  localStorage.setItem("downloadHistory", JSON.stringify(history));
  renderHistory();
}

function renderHistory() {
  const history = JSON.parse(localStorage.getItem("downloadHistory") || "[]");
  if (!history.length) {
    historyDiv.innerHTML = '<div class="history-item">No downloads yet</div>';
    return;
  }
  historyDiv.innerHTML = history.map(h => 
    `<div class="history-item"><strong>${escapeHtml(h.name)}</strong><small>${escapeHtml(h.file)} • ${h.time}</small></div>`
  ).join("");
}

window.toggleTheme = toggleTheme;
window.getInfo = getInfo;
window.selectQuality = selectQuality;
window.onDownloadClick = onDownloadClick;
window.chooseFolderAndStart = chooseFolderAndStart;
window.closeFolderModal = closeFolderModal;
