const API = "http://127.0.0.1:8000/api";

async function getInfo() {
    const url = document.getElementById("url").value;

    const res = await fetch(`${API}/metadata?url=${encodeURIComponent(url)}`);
    const data = await res.json();

    document.getElementById("info").innerHTML = `
        <h2>${data.title}</h2>
        <img src="${data.thumbnail}">
        <button onclick="downloadVideo('${url}')">Download Video</button>
    `;
}

async function downloadVideo(url) {
    const res = await fetch(`${API}/download?url=${encodeURIComponent(url)}`);
    const data = await res.json();

    alert("Video downloaded to: " + data.file);
}
