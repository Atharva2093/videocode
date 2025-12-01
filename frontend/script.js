const API = "http://127.0.0.1:8000/api";

let selectedFolder = null;

const urlInput = document.getElementById("url");
const infoDiv = document.getElementById("info");
const loading = document.getElementById("loading");
const errorDiv = document.getElementById("error");
const historyDiv = document.getElementById("history");
const progressContainer = document.getElementById("progressContainer");
const progressBar = document.getElementById("progressBar");

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

/* ---------- FETCH METADATA ---------- */
async function getInfo() {
    const url = urlInput.value.trim();
    errorDiv.textContent = "";
    infoDiv.innerHTML = "";

    if (!url) {
        errorDiv.textContent = "Please paste a YouTube URL.";
        return;
    }

    loading.classList.remove("hidden");

    try {
        const res = await fetch(`${API}/metadata?url=${encodeURIComponent(url)}`);
        const data = await res.json();

        loading.classList.add("hidden");

        if (data.detail || data.error) {
            errorDiv.textContent = data.error || "Invalid video or DRM protected.";
            return;
        }

        infoDiv.innerHTML = `
            <div class="video-card">
                <img src="${data.thumbnail}">
                <p class="video-title">${data.title}</p>
                <button class="btn primary" onclick="download('${encodeURIComponent(url)}', 'best')">Download MP4</button>
                <button class="btn primary" style="margin-top:10px;background:#10b981" onclick="download('${encodeURIComponent(url)}', 'mp3')">Download MP3</button>
            </div>
        `;

    } catch (error) {
        loading.classList.add("hidden");
        errorDiv.textContent = "Error fetching video.";
    }
}

/* ---------- DOWNLOAD WITH PROGRESS ---------- */
async function download(encodedUrl, format) {
    const url = decodeURIComponent(encodedUrl);
    progressContainer.classList.remove("hidden");
    progressBar.style.width = "0%";

    // Simulated progress
    let progress = 0;
    const interval = setInterval(() => {
        if (progress < 90) {
            progress += 5;
            progressBar.style.width = progress + "%";
        }
    }, 200);

    try {
        const downloadUrl = `${API}/download?url=${encodeURIComponent(url)}&format_id=${format}`;

        // If folder selected → save to that folder
        if (selectedFolder) {
            await saveToSelectedFolder(downloadUrl);
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
            progressContainer.classList.add("hidden");
        }, 1500);

    } catch (error) {
        clearInterval(interval);
        progressContainer.classList.add("hidden");
        errorDiv.textContent = "Error downloading video.";
    }
}

/* ---------- SAVE FILE TO SELECTED FOLDER ---------- */
async function saveToSelectedFolder(fileURL) {
    try {
        const response = await fetch(fileURL);
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
