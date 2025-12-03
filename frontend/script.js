"use strict";

const isLocalHost = ["localhost", "127.0.0.1", "::1", "0.0.0.0"].includes(location.hostname);
const API = isLocalHost ? "http://127.0.0.1:8000/api" : "https://yt-downloader-backend-ogpx.onrender.com/api";

const state = {
  currentUrl: "",
  currentTitle: "",
  metadata: null,
  selectedFormatId: null,
};

const $ = (id) => document.getElementById(id);
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
const statusBanner = $("statusBanner");
const statusSpinner = $("statusSpinner");
const statusIcon = $("statusIcon");
const statusText = $("statusText");
const folderModal = $("folderModal");
const historyDiv = $("history");
const connectionStatus = $("connectionStatus");
const toastContainer = $("toastContainer");
const floatingProgress = $("floatingProgress");
const floatingProgressText = $("floatingProgressText");

const STATUS_CLASS_MAP = {
  info: "",
  preparing: "progress",
  progress: "progress",
  success: "success",
  error: "error",
};

const STATUS_ICON_MAP = {
  info: "ℹ️",
  progress: "⬇️",
  success: "✅",
  error: "❌",
};

document.addEventListener("DOMContentLoaded", () => {
  loadTheme();
  renderHistory();
  checkConnection();
  setInterval(checkConnection, 30000);

  urlInput.addEventListener("keypress", (event) => {
    if (event.key === "Enter") {
      getInfo();
    }
  });

  urlInput.addEventListener("input", () => {
    hideError();
    hideStatus();
  });

  folderModal.addEventListener("click", (event) => {
    if (event.target === folderModal) {
      closeFolderModal();
      setDownloadState("idle");
    }
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      closeFolderModal();
      setDownloadState("idle");
    }
  });
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
    /^(https?:\/\/)?(www\.)?youtube\.com\/embed\/[\w-]{11}/,
  ];
  return patterns.some((pattern) => pattern.test(url.trim()));
}

function showStatus(message, state = "info") {
  statusBanner.classList.remove("hidden");
  statusBanner.className = "status-banner";
  const classSuffix = STATUS_CLASS_MAP[state] || "";
  if (classSuffix) statusBanner.classList.add(classSuffix);

  statusSpinner.classList.add("hidden");
  statusIcon.classList.add("hidden");

  if (state === "preparing") {
    statusSpinner.classList.remove("hidden");
    statusIcon.classList.add("hidden");
  } else {
    const icon = STATUS_ICON_MAP[state] || STATUS_ICON_MAP.info;
    statusIcon.textContent = icon;
    statusIcon.classList.remove("hidden");
  }

  statusText.textContent = message;
}

function hideStatus() {
  statusBanner.classList.add("hidden");
  statusBanner.className = "status-banner";
}

function showError(message, hint = "") {
  errorBox.classList.remove("hidden");
  errorMessage.textContent = message;
  errorHint.textContent = hint;
  showStatus(message, "error");
  successBox.classList.add("hidden");
}

function hideError() {
  errorBox.classList.add("hidden");
}

function showToast(message, type = "info", duration = 3500) {
  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  const icon = type === "success" ? "✅" : type === "error" ? "❌" : "ℹ️";
  toast.innerHTML = `<span>${icon}</span><span>${message}</span>`;
  toastContainer.appendChild(toast);
  setTimeout(() => toast.remove(), duration);
}

async function checkConnection() {
  try {
    const response = await fetch(`${API}/health`, { cache: "no-store" });
    const data = await response.json();
    if (data.status === "ok") {
      connectionStatus.textContent = "● Connected";
      connectionStatus.className = "status-badge online";
    } else {
      throw new Error("Service unavailable");
    }
  } catch (error) {
    connectionStatus.textContent = "● Offline";
    connectionStatus.className = "status-badge offline";
  }
}

async function getInfo() {
  hideError();
  hideStatus();
  successBox.classList.add("hidden");
  infoDiv.innerHTML = "";
  qualitySelector.classList.add("hidden");
  qualitySelector.innerHTML = "";
  downloadBtn.classList.add("hidden");
  state.selectedFormatId = null;

  const url = urlInput.value.trim();
  if (!url) return showError("Please enter a YouTube URL.");
  if (!isValidUrl(url)) return showError("Invalid YouTube URL.", "Check the format and try again.");

  loading.classList.remove("hidden");

  const attempts = 2;
  let data = null;

  for (let attempt = 0; attempt < attempts; attempt += 1) {
    try {
      const response = await fetch(`${API}/metadata?url=${encodeURIComponent(url)}`);
      data = await response.json();
      if (data?.error) throw new Error(data.message || "Failed to fetch info");
      break;
    } catch (error) {
      if (attempt === attempts - 1) {
        loading.classList.add("hidden");
        return showError(error.message || "Could not fetch video info.", "Check your connection or try again.");
      }
      await new Promise((resolve) => setTimeout(resolve, 900));
    }
  }

  loading.classList.add("hidden");

  if (!data?.title) return showError("Could not load video metadata.", "Try a different video.");

  state.currentUrl = url;
  state.currentTitle = data.title;
  state.metadata = data;

  renderVideoInfo(data);
  renderQualityChips(data.video_formats || []);
  downloadBtn.classList.remove("hidden");
  showStatus("Ready to download — choose a quality and click Download.", "info");
}

function renderVideoInfo(info) {
  const durationLabel = info.duration ? formatDuration(info.duration) : "";
  const channel = escapeHtml(info.channel || "");
  const title = escapeHtml(info.title || "");
  const thumbnail = escapeHtml(info.thumbnail || "");

  infoDiv.innerHTML = `
    <div class="video-card">
      <img src="${thumbnail}" alt="Thumbnail" onerror="this.style.display='none'">
      <div class="video-info">
        <p class="video-title">${title}</p>
        <p class="video-meta">${channel}${durationLabel ? ` • ${durationLabel}` : ""}</p>
      </div>
    </div>
  `;
}

function renderQualityChips(formats) {
  if (!Array.isArray(formats)) formats = [];
  const mp4Formats = formats.filter((format) => format.ext === "mp4");
  const grouped = new Map();

  mp4Formats.forEach((format) => {
    const key = `${format.height || "unknown"}p`;
    if (!grouped.has(key)) {
      grouped.set(key, format);
      return;
    }
    const current = grouped.get(key);
    if (!current.has_audio && format.has_audio) {
      grouped.set(key, format);
    }
  });

  const qualities = [...grouped.entries()]
    .filter(([height]) => height !== "unknownp")
    .sort((a, b) => parseInt(b[0], 10) - parseInt(a[0], 10));

  qualitySelector.innerHTML = "";

  if (!qualities.length) {
    const fallback = document.createElement("button");
    fallback.className = "quality-chip active";
    fallback.dataset.formatId = "best";
    fallback.textContent = "Best Available";
    fallback.addEventListener("click", () => selectQualityButton(fallback));
    qualitySelector.appendChild(fallback);
    state.selectedFormatId = "best";
  } else {
    const defaultQuality = qualities.find(([quality]) => quality === "720p") || qualities[0];
    qualities.forEach(([label, format]) => {
      const btn = document.createElement("button");
      btn.className = `quality-chip${label === defaultQuality[0] ? " active" : ""}`;
      btn.dataset.formatId = format.format_id || "best";
      btn.textContent = label;
      btn.addEventListener("click", () => selectQualityButton(btn));
      qualitySelector.appendChild(btn);
      if (label === defaultQuality[0]) state.selectedFormatId = format.format_id || "best";
    });
  }

  qualitySelector.classList.remove("hidden");
}

function selectQualityButton(button) {
  document.querySelectorAll(".quality-chip").forEach((chip) => chip.classList.remove("active"));
  button.classList.add("active");
  state.selectedFormatId = button.dataset.formatId;
}

function onDownloadClick() {
  hideError();
  successBox.classList.add("hidden");

  if (!state.currentUrl) return showError("No video selected.", "Fetch a video first.");
  if (!state.metadata) return showError("Metadata missing.", "Fetch the video again.");
  if (!state.selectedFormatId) return showError("No quality selected.");

  if (typeof window.showDirectoryPicker !== "function") {
    return showError("Browser not supported.", "Use Chrome or Edge.");
  }

  folderModal.classList.remove("hidden");
}

function closeFolderModal() {
  folderModal.classList.add("hidden");
}

async function chooseFolderAndStart() {
  closeFolderModal();
  setDownloadState("preparing");
  showStatus("Waiting for folder selection…", "preparing");

  let folderHandle;
  try {
    folderHandle = await window.showDirectoryPicker({ mode: "readwrite" });
  } catch (error) {
    hideStatus();
    setDownloadState("idle");
    resetProgress();
    floatingProgress.classList.add("hidden");
    if (error?.name !== "AbortError") {
      showToast("Folder selection failed", "error");
    }
    return;
  }

  await downloadToFolder(folderHandle);
}

async function downloadToFolder(folderHandle) {
  hideError();
  successBox.classList.add("hidden");
  resetProgress();

  floatingProgress.classList.remove("hidden");
  progressContainer.classList.remove("hidden");
  showStatus("Preparing download…", "preparing");
  showToast("Preparing download…", "info", 2200);

  let writable;
  let reader;
  let response;
  const folderName = folderHandle?.name || "selected folder";

  try {
    response = await fetch(`${API}/download?url=${encodeURIComponent(state.currentUrl)}&format_id=${encodeURIComponent(state.selectedFormatId || "best")}`);

    const contentType = response.headers.get("Content-Type") || "";
    if (contentType.includes("application/json")) {
      const errorPayload = await response.json();
      throw new Error(errorPayload.message || "Download failed.");
    }

    if (!response.ok) throw new Error(`Server error (${response.status})`);
    if (!response.body) throw new Error("No data received from server.");

    const disposition = response.headers.get("Content-Disposition") || "";
    const filename = resolveFilename(disposition, state.currentTitle);
    const fileHandle = await folderHandle.getFileHandle(filename, { create: true });
    writable = await fileHandle.createWritable();

    const total = parseInt(response.headers.get("Content-Length") || "0", 10);
    reader = response.body.getReader();
    let received = 0;

    setDownloadState("downloading");

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      await writable.write(value);
      received += value.length;
      updateProgress(received, total);
    }

    await writable.close();
    updateProgressComplete(total > 0);

    successBox.innerHTML = `✅ Download complete — saved to: <strong>${escapeHtml(folderName)}</strong>`;
    successBox.classList.remove("hidden");
    showStatus(`Download complete — saved to: ${folderName}`, "success");
    showToast(`Download completed: ${filename}`, "success", 4500);
    playSound();
    saveToHistory(state.currentTitle, filename, folderName);

    setDownloadState("completed");
    setTimeout(() => {
      setDownloadState("idle");
      resetProgress();
      floatingProgress.classList.add("hidden");
    }, 2500);
  } catch (error) {
    if (reader) {
      try { reader.cancel(); } catch (_) { /* ignore */ }
    }
    if (writable) {
      try { await writable.abort(); } catch (_) { /* ignore */ }
    }
    floatingProgress.classList.add("hidden");
    progressContainer.classList.add("hidden");
    resetProgress();
    setDownloadState("idle");
    showStatus(error.message || "Download failed.", "error");
    showError(error.message || "Download failed.", "Please try again.");
    showToast("Failed to download video", "error", 4000);
  }
}

function updateProgress(received, total) {
  if (total > 0) {
    const percentage = Math.min(99, Math.round((received / total) * 100));
    progressBar.style.width = `${percentage}%`;
    progressPercent.textContent = `${percentage}%`;
    floatingProgressText.textContent = `${percentage}%`;
    showStatus(`Downloading… ${percentage}%`, "progress");
  } else {
    const megabytes = (received / 1048576).toFixed(1);
    progressBar.style.width = "90%";
    progressPercent.textContent = `${megabytes} MB`;
    floatingProgressText.textContent = `${megabytes} MB`;
    showStatus(`Downloading… ${megabytes} MB`, "progress");
  }
}

function updateProgressComplete(hasKnownSize) {
  progressBar.style.width = "100%";
  progressPercent.textContent = hasKnownSize ? "100%" : "Done";
  floatingProgressText.textContent = hasKnownSize ? "100%" : "Done";
}

function resetProgress() {
  progressBar.style.width = "0%";
  progressPercent.textContent = "0%";
  progressContainer.classList.add("hidden");
}

function setDownloadState(state) {
  downloadBtn.classList.remove("downloading", "completed");
  if (state === "preparing") {
    downloadBtn.textContent = "⏳ Preparing…";
    downloadBtn.classList.add("downloading");
    downloadBtn.disabled = true;
  } else if (state === "downloading") {
    downloadBtn.textContent = "⬇️ Downloading…";
    downloadBtn.classList.add("downloading");
    downloadBtn.disabled = true;
  } else if (state === "completed") {
    downloadBtn.textContent = "✅ Downloaded!";
    downloadBtn.classList.add("completed");
    downloadBtn.disabled = true;
  } else {
    downloadBtn.textContent = "⬇️ Download MP4";
    downloadBtn.disabled = false;
  }
}

function resolveFilename(disposition, title) {
  const fallback = `${sanitizeForFilename(title)}.mp4`;
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
  const cleanBase = sanitizeForFilename(base);
  const cleanExt = sanitizeForFilename(ext).toLowerCase() || "mp4";
  return `${cleanBase}.${cleanExt}`;
}

function sanitizeForFilename(name) {
  if (!name) return "video";
  return name.replace(/[\\/:*?"<>|]/g, "").replace(/\s+/g, " ").trim().substring(0, 150) || "video";
}

function escapeHtml(text) {
  const element = document.createElement("div");
  element.textContent = text ?? "";
  return element.innerHTML;
}

function formatDuration(seconds) {
  const mins = Math.floor(seconds / 60);
  const secs = String(seconds % 60).padStart(2, "0");
  return `${mins}:${secs}`;
}

function playSound() {
  try {
    const context = new (window.AudioContext || window.webkitAudioContext)();
    const osc = context.createOscillator();
    const gain = context.createGain();
    osc.connect(gain);
    gain.connect(context.destination);
    osc.type = "triangle";
    osc.frequency.setValueAtTime(880, context.currentTime);
    osc.frequency.exponentialRampToValueAtTime(1320, context.currentTime + 0.18);
    gain.gain.setValueAtTime(0.12, context.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, context.currentTime + 0.25);
    osc.start();
    osc.stop(context.currentTime + 0.25);
  } catch (_) {
    /* ignore */
  }
}

function saveToHistory(title, filename, folderName) {
  const history = JSON.parse(localStorage.getItem("downloadHistory") || "[]");
  const entry = {
    name: (title || filename || "Video").substring(0, 80),
    file: filename,
    folder: folderName,
    time: new Date().toLocaleString(),
  };
  history.unshift(entry);
  const unique = [];
  const seen = new Set();
  history.forEach((item) => {
    if (seen.has(item.file)) return;
    seen.add(item.file);
    unique.push(item);
  });
  while (unique.length > 10) unique.pop();
  localStorage.setItem("downloadHistory", JSON.stringify(unique));
  renderHistory();
}

function renderHistory() {
  const history = JSON.parse(localStorage.getItem("downloadHistory") || "[]");
  if (!history.length) {
    historyDiv.innerHTML = '<div class="history-item">No downloads yet</div>';
    return;
  }

  historyDiv.innerHTML = history
    .map((item) => `
      <div class="history-item">
        <strong>${escapeHtml(item.name)}</strong>
        <small>${escapeHtml(item.file)} • ${escapeHtml(item.folder || "folder")} • ${item.time}</small>
      </div>
    `)
    .join("");
}

window.toggleTheme = toggleTheme;
window.getInfo = getInfo;
window.selectQuality = selectQualityButton;
window.onDownloadClick = onDownloadClick;
window.chooseFolderAndStart = chooseFolderAndStart;
window.closeFolderModal = closeFolderModal;
