const API = "https://yt-downloader-backend.onrender.com/api";

let selectedFolder = null;
let selectedFormat = "mp4";
let selectedQuality = "720p";
let currentVideoUrl = "";
let availableQualities = [];

const urlInput = document.getElementById("url");
const infoDiv = document.getElementById("info");
const loading = document.getElementById("loading");
const historyDiv = document.getElementById("history");
const progressContainer = document.getElementById("progressContainer");
const progressBar = document.getElementById("progressBar");
const qualitySelector = document.getElementById("qualitySelector");
const downloadBtn = document.getElementById("downloadBtn");
const errorBox = document.getElementById("errorBox");
const errorMessage = document.getElementById("errorMessage");
const errorHint = document.getElementById("errorHint");

/* ---------- ERROR HANDLING ---------- */
function showError(message, hint = "") {
    errorMessage.textContent = message;
    errorHint.textContent = hint;
    errorBox.classList.remove("hidden");
}

function hideError() {
    errorBox.classList.add("hidden");
    errorMessage.textContent = "";
    errorHint.textContent = "";
}

/* ---------- CLEAR ERRORS ON INPUT ---------- */
urlInput.addEventListener("input", hideError);
urlInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter") {
        hideError();
        getInfo();
    }
});

/* ---------- DARK MODE ---------- */
function toggleTheme() {
    const html = document.documentElement;
    html.dataset.theme = html.dataset.theme === "dark" ? "light" : "dark";
}

/* ---------- URL AUTODETECT (Clipboard) ---------- */
document.addEventListener("click", async () => {
    try {
        const text = await navigator.clipboard.readText();
        if (text.includes("youtube.com") || text.includes("youtu.be")) {
            urlInput.value = text;
        }
    } catch (err) {
        console.log("Clipboard read blocked");
    }
});

/* ---------- SELECT DOWNLOAD FOLDER ---------- */
async function selectFolder() {
    if (!window.showDirectoryPicker) {
        alert("Folder selection is only supported in Chrome / Edge.");
        return;
    }

    try {
        selectedFolder = await window.showDirectoryPicker();
        localStorage.setItem("downloadFolder", "selected");

        document.getElementById("folderPath").textContent = "Folder selected ✔";
        alert("Folder selected successfully!");

    } catch (err) {
        console.log(err);
        alert("Folder selection cancelled.");
    }
}

/* ---------- FORMAT SELECTION ---------- */
function setFormat(format) {
    selectedFormat = format;
    document.getElementById("btnMp4").classList.toggle("active", format === "mp4");
    document.getElementById("btnMp3").classList.toggle("active", format === "mp3");
    
    // Show/hide quality selector (only for MP4)
    if (format === "mp4" && availableQualities.length > 0) {
        qualitySelector.classList.remove("hidden");
    } else {
        qualitySelector.classList.add("hidden");
    }
}

/* ---------- QUALITY SELECTION ---------- */
function setQuality(quality) {
    selectedQuality = quality;
    document.querySelectorAll(".quality-chip").forEach(chip => {
        chip.classList.toggle("active", chip.dataset.quality === quality);
    });
}

/* ---------- RENDER QUALITY CHIPS ---------- */
function renderQualityChips(formats) {
    // Extract available qualities from formats
    const qualitySet = new Set();
    formats.forEach(f => {
        if (f.height) {
            qualitySet.add(f.height + "p");
        }
    });
    
    availableQualities = Array.from(qualitySet).sort((a, b) => parseInt(b) - parseInt(a));
    
    // Default to 720p or highest available
    if (availableQualities.includes("720p")) {
        selectedQuality = "720p";
    } else if (availableQualities.length > 0) {
        selectedQuality = availableQualities[0];
    }
    
    qualitySelector.innerHTML = availableQualities.map(q => 
        `<button class="quality-chip ${q === selectedQuality ? 'active' : ''}" data-quality="${q}" onclick="setQuality('${q}')">${q}</button>`
    ).join("");
}

/* ---------- FETCH METADATA ---------- */
async function getInfo() {
    const url = urlInput.value.trim();
    hideError();
    infoDiv.innerHTML = "";
    qualitySelector.classList.add("hidden");
    downloadBtn.classList.add("hidden");

    if (!url) {
        showError("Please enter a YouTube URL.", "Example: https://youtu.be/xxxx");
        return;
    }

    // Basic URL validation
    if (!url.includes("youtube.com") && !url.includes("youtu.be")) {
        showError("Invalid URL format.", "Please enter a valid YouTube link.");
        return;
    }

    loading.classList.remove("hidden");

    try {
        const res = await fetch(`${API}/metadata?url=${encodeURIComponent(url)}`);
        const data = await res.json();

        loading.classList.add("hidden");

        // Handle standardized error response
        if (data.error) {
            showError(data.message || data.error, data.hint || "");
            return;
        }

        currentVideoUrl = url;

        // Render video card
        infoDiv.innerHTML = `
            <div class="video-card">
                <img src="${data.thumbnail}">
                <p class="video-title">${data.title}</p>
            </div>
        `;

        // Render quality chips for MP4
        if (data.formats && data.formats.length > 0) {
            renderQualityChips(data.formats);
            if (selectedFormat === "mp4") {
                qualitySelector.classList.remove("hidden");
            }
        }

        // Show download button
        downloadBtn.classList.remove("hidden");

    } catch (error) {
        loading.classList.add("hidden");
        showError("Could not connect to server.", "Check your internet connection and try again.");
    }
}

/* ---------- START DOWNLOAD ---------- */
function startDownload() {
    const formatId = selectedFormat === "mp3" ? "mp3" : `best[height<=${parseInt(selectedQuality)}]`;
    download(currentVideoUrl, formatId);
}

/* ---------- DOWNLOAD WITH PROGRESS ---------- */
async function download(url, format) {
    hideError();
    progressContainer.classList.remove("hidden");
    progressBar.style.width = "0%";
    progressBar.classList.add("animated");

    // Animated progress
    let progress = 0;
    const interval = setInterval(() => {
        if (progress < 90) {
            progress += Math.random() * 8;
            progressBar.style.width = Math.min(progress, 90) + "%";
        }
    }, 300);

    try {
        const downloadUrl = `${API}/download?url=${encodeURIComponent(url)}&format_id=${format}`;

        // If folder selected → save to that folder
        if (selectedFolder) {
            const response = await fetch(downloadUrl);
            
            // Check for error response (JSON)
            const contentType = response.headers.get("content-type");
            if (contentType && contentType.includes("application/json")) {
                const data = await response.json();
                if (data.error) {
                    clearInterval(interval);
                    progressBar.classList.remove("animated");
                    progressContainer.classList.add("hidden");
                    showError(data.message || data.error, data.hint || "");
                    return;
                }
            }
            
            await saveToSelectedFolder(downloadUrl, response);
            clearInterval(interval);
            progressBar.style.width = "100%";
            
            const title = document.querySelector('.video-title')?.textContent || url;
            saveToHistory(title);
            alert("Downloaded to selected folder!");
        } else {
            // Default browser download
            clearInterval(interval);
            progressBar.style.width = "100%";
            
            const title = document.querySelector('.video-title')?.textContent || url;
            saveToHistory(title);
            
            window.location.href = downloadUrl;
        }

        setTimeout(() => {
            progressBar.classList.remove("animated");
            progressContainer.classList.add("hidden");
        }, 1500);

    } catch (error) {
        clearInterval(interval);
        progressBar.classList.remove("animated");
        progressContainer.classList.add("hidden");
        showError("Download failed.", "Check your connection and try again.");
    }
}

/* ---------- SAVE FILE TO SELECTED FOLDER ---------- */
async function saveToSelectedFolder(fileURL, existingResponse = null) {
    try {
        const response = existingResponse || await fetch(fileURL);
        const blob = await response.blob();

        // Extract filename from Content-Disposition or URL
        const contentDisposition = response.headers.get('Content-Disposition');
        let fileName = 'video.mp4';
        if (contentDisposition) {
            const match = contentDisposition.match(/filename="?([^"]+)"?/);
            if (match) fileName = match[1];
        } else {
            fileName = fileURL.split("/").pop().split("?")[0] || 'video.mp4';
        }

        const fileHandle = await selectedFolder.getFileHandle(fileName, { create: true });
        const writable = await fileHandle.createWritable();

        await writable.write(blob);
        await writable.close();

        console.log("Saved to selected folder:", fileName);
    } catch (err) {
        console.log(err);
        alert("Unable to save directly. Falling back to normal download.");
        window.location.href = fileURL;
    }
}

/* ---------- RECENT DOWNLOAD HISTORY ---------- */
function saveToHistory(file) {
    let history = JSON.parse(localStorage.getItem("history") || "[]");
    history.unshift({ file, time: new Date().toLocaleString() });
    if (history.length > 5) history.pop();
    localStorage.setItem("history", JSON.stringify(history));
    renderHistory();
}

function renderHistory() {
    let history = JSON.parse(localStorage.getItem("history") || "[]");
    historyDiv.innerHTML = history
        .map(h => `<div class="history-item">${h.file}<br><small>${h.time}</small></div>`)
        .join("");
}

renderHistory();
