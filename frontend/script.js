const API =
    location.hostname.includes("localhost") || location.hostname.includes("127.")
        ? "http://127.0.0.1:8000/api"
        : "https://yt-downloader-backend-ogpx.onrender.com/api";

console.log("DEBUG: Using API =", API);

/* -------------------------------------------
   GLOBAL VARIABLES
-------------------------------------------- */
let selectedFolder = null;
let selectedFormat = "mp4";
let selectedQuality = "720p";
let currentVideoUrl = "";
let availableQualities = [];

/* -------------------------------------------
   DOM ELEMENTS
-------------------------------------------- */
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

/* -------------------------------------------
   ERROR HANDLING
-------------------------------------------- */
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

urlInput.addEventListener("input", hideError);
urlInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter") {
        hideError();
        getInfo();
    }
});

/* -------------------------------------------
   DARK MODE
-------------------------------------------- */
function toggleTheme() {
    const html = document.documentElement;
    html.dataset.theme = html.dataset.theme === "dark" ? "light" : "dark";
}

/* -------------------------------------------
   CLIPBOARD AUTO-DETECT (Mobile + Desktop)
-------------------------------------------- */
document.addEventListener("click", async () => {
    try {
        const text = await navigator.clipboard.readText();
        if (text.includes("youtube.com") || text.includes("youtu.be")) {
            urlInput.value = text;
        }
    } catch (err) {
        console.log("Clipboard access denied");
    }
});

/* -------------------------------------------
   SELECT FOLDER
-------------------------------------------- */
async function selectFolder() {
    if (!window.showDirectoryPicker) {
        alert("Folder selection is only supported in Chrome / Edge.");
        return;
    }

    try {
        selectedFolder = await window.showDirectoryPicker();
        document.getElementById("folderPath").textContent = "Folder selected ✔";
        alert("Folder selected!");
    } catch (err) {
        console.log(err);
        alert("Folder selection cancelled.");
    }
}

/* -------------------------------------------
   FORMAT (MP4 / MP3)
-------------------------------------------- */
function setFormat(format) {
    selectedFormat = format;

    document.getElementById("btnMp4").classList.toggle("active", format === "mp4");
    document.getElementById("btnMp3").classList.toggle("active", format === "mp3");

    if (format === "mp4" && availableQualities.length > 0) {
        qualitySelector.classList.remove("hidden");
    } else {
        qualitySelector.classList.add("hidden");
    }
}

/* -------------------------------------------
   QUALITY SELECTOR
-------------------------------------------- */
function setQuality(quality) {
    selectedQuality = quality;
    document.querySelectorAll(".quality-chip").forEach((chip) => {
        chip.classList.toggle("active", chip.dataset.quality === quality);
    });
}

/* -------------------------------------------
   RENDER QUALITY BUTTONS
-------------------------------------------- */
function renderQualityChips(formats) {
    const qualitySet = new Set();

    formats.forEach((f) => {
        if (f.height) qualitySet.add(f.height + "p");
    });

    availableQualities = Array.from(qualitySet).sort(
        (a, b) => parseInt(b) - parseInt(a)
    );

    selectedQuality = availableQualities.includes("720p")
        ? "720p"
        : availableQualities[0] || "360p";

    qualitySelector.innerHTML = availableQualities
        .map(
            (q) =>
                `<button class="quality-chip ${q === selectedQuality ? "active" : ""}" data-quality="${q}" onclick="setQuality('${q}')">${q}</button>`
        )
        .join("");
}

/* -------------------------------------------
   FETCH VIDEO INFO
-------------------------------------------- */
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

    loading.classList.remove("hidden");

    try {
        const res = await fetch(`${API}/metadata?url=${encodeURIComponent(url)}`);
        const data = await res.json();

        loading.classList.add("hidden");

        if (data.error) {
            showError(data.message || data.error, data.hint);
            return;
        }

        currentVideoUrl = url;

        infoDiv.innerHTML = `
            <div class="video-card">
                <img src="${data.thumbnail}">
                <p class="video-title">${data.title}</p>
            </div>
        `;

        if (data.formats) {
            renderQualityChips(data.formats);
            if (selectedFormat === "mp4") {
                qualitySelector.classList.remove("hidden");
            }
        }

        downloadBtn.classList.remove("hidden");
    } catch (err) {
        loading.classList.add("hidden");
        showError("Could not connect to server.", "Check your internet connection.");
    }
}

/* -------------------------------------------
   START DOWNLOAD
-------------------------------------------- */
function startDownload() {
    const formatId =
        selectedFormat === "mp3"
            ? "mp3"
            : `best[height<=${parseInt(selectedQuality)}]`;

    download(currentVideoUrl, formatId);
}

/* -------------------------------------------
   DOWNLOAD VIDEO
-------------------------------------------- */
async function download(url, format) {
    hideError();
    progressContainer.classList.remove("hidden");
    progressBar.style.width = "0%";

    let fakeProgress = 0;
    const interval = setInterval(() => {
        fakeProgress = Math.min(fakeProgress + Math.random() * 10, 90);
        progressBar.style.width = fakeProgress + "%";
    }, 300);

    try {
        const downloadUrl = `${API}/download?url=${encodeURIComponent(
            url
        )}&format_id=${format}`;

        if (selectedFolder) {
            const response = await fetch(downloadUrl);
            const type = response.headers.get("content-type");

            if (type?.includes("json")) {
                const err = await response.json();
                clearInterval(interval);
                showError(err.message, err.hint);
                return;
            }

            await saveToSelectedFolder(downloadUrl, response);
        } else {
            window.location.href = downloadUrl;
        }

        clearInterval(interval);
        progressBar.style.width = "100%";

        saveToHistory(document.querySelector(".video-title")?.textContent || url);

        setTimeout(() => {
            progressContainer.classList.add("hidden");
        }, 1500);
    } catch (err) {
        clearInterval(interval);
        showError("Download failed.", "Please try again.");
    }
}

/* -------------------------------------------
   SAVE FILE IN CHOSEN FOLDER
-------------------------------------------- */
async function saveToSelectedFolder(url, response) {
    const blob = await response.blob();
    const fileName = "video.mp4";

    const handle = await selectedFolder.getFileHandle(fileName, { create: true });
    const writable = await handle.createWritable();
    await writable.write(blob);
    await writable.close();
}

/* -------------------------------------------
   DOWNLOAD HISTORY
-------------------------------------------- */
function saveToHistory(name) {
    let h = JSON.parse(localStorage.getItem("history") || "[]");
    h.unshift({ name, time: new Date().toLocaleString() });
    if (h.length > 5) h.pop();
    localStorage.setItem("history", JSON.stringify(h));
    renderHistory();
}

function renderHistory() {
    let h = JSON.parse(localStorage.getItem("history") || "[]");
    historyDiv.innerHTML = h
        .map(
            (x) =>
                `<div class="history-item">${x.name}<br><small>${x.time}</small></div>`
        )
        .join("");
}

renderHistory();
