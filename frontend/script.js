const API = "http://127.0.0.1:8000/api";

function showError(message) {
    document.getElementById("errorMessage").textContent = message;
    document.getElementById("errorModal").style.display = "flex";
}

function closeModal() {
    document.getElementById("errorModal").style.display = "none";
}

function showLoading(show) {
    document.getElementById("loading").style.display = show ? "block" : "none";
}

async function getInfo() {
    const url = document.getElementById("url").value.trim();
    
    if (!url) {
        showError("Please enter a YouTube URL");
        return;
    }
    
    showLoading(true);
    document.getElementById("info").innerHTML = "";
    
    try {
        const res = await fetch(`${API}/metadata?url=${encodeURIComponent(url)}`);
        const data = await res.json();
        
        if (data.error) {
            showError(data.error);
            showLoading(false);
            return;
        }
        
        showLoading(false);
        document.getElementById("info").innerHTML = `
            <h2>${data.title}</h2>
            <img src="${data.thumbnail}" alt="Thumbnail">
            ${data.duration ? `<p>Duration: ${Math.floor(data.duration / 60)}:${(data.duration % 60).toString().padStart(2, '0')}</p>` : ''}
            <button onclick="downloadVideo('${encodeURIComponent(url)}')">Download Video</button>
        `;
    } catch (err) {
        showLoading(false);
        showError("Failed to connect to server. Make sure the backend is running.");
    }
}

function downloadVideo(encodedUrl) {
    // Decode then re-encode to ensure proper formatting
    const url = decodeURIComponent(encodedUrl);
    showLoading(true);
    
    // Create a hidden iframe to trigger download without leaving page
    const downloadUrl = `${API}/download?url=${encodeURIComponent(url)}`;
    
    // Use fetch to check for errors first
    fetch(downloadUrl)
        .then(response => {
            if (!response.ok) {
                return response.json().then(data => {
                    throw new Error(data.error || "Download failed");
                });
            }
            // If response is OK, trigger actual download
            window.location.href = downloadUrl;
            showLoading(false);
        })
        .catch(err => {
            showLoading(false);
            showError(err.message || "Download failed. This video may be restricted or DRM-protected.");
        });
}

// Close modal when clicking outside
window.onclick = function(event) {
    const modal = document.getElementById("errorModal");
    if (event.target === modal) {
        closeModal();
    }
}
