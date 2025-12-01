const API = "http://127.0.0.1:8000/api";

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

    // Simulated progress (backend does not send progress)
    let progress = 0;
    const interval = setInterval(() => {
        if (progress < 90) {
            progress += 5;
            progressBar.style.width = progress + "%";
        }
    }, 200);

    try {
        // Trigger download via browser navigation
        const downloadUrl = `${API}/download?url=${encodeURIComponent(url)}&format_id=${format}`;
        
        // Check if download will work first
        const res = await fetch(downloadUrl, { method: 'HEAD' }).catch(() => null);
        
        clearInterval(interval);
        progressBar.style.width = "100%";
        
        // Save to history
        const title = document.querySelector('.video-title')?.textContent || url;
        saveToHistory(title);
        
        // Trigger actual download
        window.location.href = downloadUrl;
        
        setTimeout(() => {
            progressContainer.classList.add("hidden");
        }, 1500);

    } catch (error) {
        clearInterval(interval);
        progressContainer.classList.add("hidden");
        errorDiv.textContent = "Error downloading video.";
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
