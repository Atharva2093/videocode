/**
 * YouTube Downloader - Main Application
 */

class App {
    constructor() {
        this.currentVideoInfo = null;
        this.playlistItems = [];
        this.selectedPlaylistItems = new Set();
        this.activeTasks = new Map();
        this.pollInterval = null;

        this.init();
    }

    init() {
        this.bindElements();
        this.bindEvents();
        this.checkAPIStatus();
        this.startQueuePolling();
    }

    bindElements() {
        // Input elements
        this.urlInput = document.getElementById('url-input');
        this.previewBtn = document.getElementById('preview-btn');
        this.downloadBtn = document.getElementById('download-btn');

        // Preview elements
        this.previewSection = document.getElementById('preview-section');
        this.thumbnail = document.getElementById('thumbnail');
        this.durationBadge = document.getElementById('duration-badge');
        this.videoTitle = document.getElementById('video-title');
        this.channelName = document.getElementById('channel-name');
        this.viewCount = document.getElementById('view-count');
        this.uploadDate = document.getElementById('upload-date');

        // Playlist elements
        this.playlistSection = document.getElementById('playlist-section');
        this.playlistCount = document.getElementById('playlist-count');
        this.playlistContainer = document.getElementById('playlist-container');
        this.selectAllBtn = document.getElementById('select-all-btn');
        this.deselectAllBtn = document.getElementById('deselect-all-btn');
        this.selectedCount = document.getElementById('selected-count');

        // Format elements
        this.formatSelect = document.getElementById('format-select');
        this.qualitySelect = document.getElementById('quality-select');
        this.formatsSection = document.getElementById('formats-section');
        this.formatsTbody = document.getElementById('formats-tbody');

        // Queue elements
        this.queueContainer = document.getElementById('queue-container');
        this.clearCompletedBtn = document.getElementById('clear-completed-btn');

        // Status elements
        this.apiStatusIndicator = document.getElementById('api-status-indicator');
        this.apiStatusText = document.getElementById('api-status-text');

        // Loading/Toast
        this.loadingOverlay = document.getElementById('loading-overlay');
        this.toastContainer = document.getElementById('toast-container');
    }

    bindEvents() {
        // Button clicks
        this.previewBtn.addEventListener('click', () => this.handlePreview());
        this.downloadBtn.addEventListener('click', () => this.handleDownload());
        this.clearCompletedBtn.addEventListener('click', () => this.handleClearCompleted());

        // Playlist controls
        this.selectAllBtn.addEventListener('click', () => this.selectAllPlaylist());
        this.deselectAllBtn.addEventListener('click', () => this.deselectAllPlaylist());

        // Enter key on URL input
        this.urlInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.handlePreview();
            }
        });

        // Format change - hide quality for audio
        this.formatSelect.addEventListener('change', () => {
            if (this.formatSelect.value === 'audio') {
                this.qualitySelect.disabled = true;
            } else {
                this.qualitySelect.disabled = false;
            }
        });
    }

    async checkAPIStatus() {
        try {
            const health = await api.checkHealth();
            this.apiStatusIndicator.classList.add('online');
            this.apiStatusIndicator.classList.remove('offline');
            this.apiStatusText.textContent = `API Online (yt-dlp ${health.yt_dlp_version || 'N/A'})`;
        } catch (error) {
            this.apiStatusIndicator.classList.add('offline');
            this.apiStatusIndicator.classList.remove('online');
            this.apiStatusText.textContent = 'API Offline';
        }
    }

    async handlePreview() {
        const url = this.urlInput.value.trim();
        if (!url) {
            this.showToast('Please enter a YouTube URL', 'error');
            return;
        }

        this.showLoading(true);
        this.previewBtn.disabled = true;

        try {
            const info = await api.getVideoInfo(url);
            this.currentVideoInfo = info;

            if (info.videos) {
                // Playlist
                this.displayPlaylistInfo(info);
            } else {
                // Single video
                this.displayVideoInfo(info);
            }

            this.previewSection.classList.remove('hidden');
        } catch (error) {
            this.showToast(`Failed to fetch video info: ${error.message}`, 'error');
        } finally {
            this.showLoading(false);
            this.previewBtn.disabled = false;
        }
    }

    displayVideoInfo(info) {
        this.thumbnail.src = info.thumbnail || '';
        this.durationBadge.textContent = info.duration_formatted || '';
        this.videoTitle.textContent = info.title || 'Unknown Title';
        this.channelName.textContent = info.channel || 'Unknown Channel';
        this.viewCount.textContent = info.view_count_formatted ? `${info.view_count_formatted} views` : '';
        this.uploadDate.textContent = info.upload_date ? this.formatDate(info.upload_date) : '';

        // Hide playlist section
        this.playlistSection.classList.add('hidden');

        // Display formats
        if (info.formats && info.formats.length > 0) {
            this.displayFormats(info.formats);
            this.formatsSection.classList.remove('hidden');
        } else {
            this.formatsSection.classList.add('hidden');
        }
    }

    displayPlaylistInfo(info) {
        this.videoTitle.textContent = info.title || 'Unknown Playlist';
        this.channelName.textContent = info.channel || '';
        this.thumbnail.src = '';
        this.durationBadge.textContent = `${info.video_count} videos`;
        this.viewCount.textContent = '';
        this.uploadDate.textContent = '';

        // Display playlist items
        this.playlistItems = info.videos || [];
        this.selectedPlaylistItems = new Set(this.playlistItems.map((_, i) => i));
        this.playlistCount.textContent = this.playlistItems.length;

        this.renderPlaylistItems();
        this.updateSelectedCount();

        this.playlistSection.classList.remove('hidden');
        this.formatsSection.classList.add('hidden');
    }

    renderPlaylistItems() {
        this.playlistContainer.innerHTML = '';

        this.playlistItems.forEach((video, index) => {
            const item = document.createElement('div');
            item.className = 'playlist-item';
            item.innerHTML = `
                <input type="checkbox" id="playlist-${index}" ${this.selectedPlaylistItems.has(index) ? 'checked' : ''}>
                <span class="playlist-item-index">${index + 1}.</span>
                <span class="playlist-item-title" title="${video.title}">${video.title}</span>
            `;

            const checkbox = item.querySelector('input');
            checkbox.addEventListener('change', () => {
                if (checkbox.checked) {
                    this.selectedPlaylistItems.add(index);
                } else {
                    this.selectedPlaylistItems.delete(index);
                }
                this.updateSelectedCount();
            });

            this.playlistContainer.appendChild(item);
        });
    }

    updateSelectedCount() {
        this.selectedCount.textContent = `${this.selectedPlaylistItems.size} selected`;
    }

    selectAllPlaylist() {
        this.selectedPlaylistItems = new Set(this.playlistItems.map((_, i) => i));
        this.renderPlaylistItems();
        this.updateSelectedCount();
    }

    deselectAllPlaylist() {
        this.selectedPlaylistItems.clear();
        this.renderPlaylistItems();
        this.updateSelectedCount();
    }

    displayFormats(formats) {
        this.formatsTbody.innerHTML = '';

        formats.forEach(format => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${format.format_id}</td>
                <td>${format.resolution || 'N/A'}</td>
                <td>${format.extension}</td>
                <td>${this.formatFilesize(format.filesize || format.filesize_approx)}</td>
            `;
            this.formatsTbody.appendChild(row);
        });
    }

    async handleDownload() {
        const url = this.urlInput.value.trim();
        if (!url) {
            this.showToast('Please enter a YouTube URL', 'error');
            return;
        }

        const format = this.formatSelect.value;
        const quality = this.qualitySelect.value;
        const audioOnly = format === 'audio';

        const downloadRequest = {
            url,
            format: audioOnly ? 'mp4' : format,
            quality,
            audio_only: audioOnly,
        };

        // Add playlist items if applicable
        if (this.playlistItems.length > 0 && this.selectedPlaylistItems.size > 0) {
            downloadRequest.playlist_items = Array.from(this.selectedPlaylistItems).map(i => i + 1);
        }

        this.downloadBtn.disabled = true;

        try {
            const response = await api.startDownload(downloadRequest);
            this.showToast(`Download queued: ${response.task_id}`, 'success');
            this.activeTasks.set(response.task_id, response);
            this.refreshQueue();
        } catch (error) {
            this.showToast(`Failed to start download: ${error.message}`, 'error');
        } finally {
            this.downloadBtn.disabled = false;
        }
    }

    async handleClearCompleted() {
        try {
            await api.clearCompleted();
            this.showToast('Cleared completed downloads', 'success');
            this.refreshQueue();
        } catch (error) {
            this.showToast(`Failed to clear: ${error.message}`, 'error');
        }
    }

    startQueuePolling() {
        this.pollInterval = setInterval(() => this.refreshQueue(), 2000);
    }

    async refreshQueue() {
        try {
            const status = await api.getQueueStatus();
            this.renderQueue(status.tasks);
        } catch (error) {
            console.error('Failed to refresh queue:', error);
        }
    }

    renderQueue(tasks) {
        if (!tasks || tasks.length === 0) {
            this.queueContainer.innerHTML = `
                <div class="queue-empty">
                    <p>No downloads in queue</p>
                </div>
            `;
            return;
        }

        this.queueContainer.innerHTML = '';

        tasks.forEach(task => {
            const item = document.createElement('div');
            item.className = 'queue-item';
            item.innerHTML = `
                <div class="queue-item-header">
                    <span class="queue-item-title">${task.title || task.task_id}</span>
                    <span class="queue-item-status status-${task.status}">${this.formatStatus(task.status)}</span>
                </div>
                <div class="progress-container">
                    <div class="progress-bar-wrapper">
                        <div class="progress-bar" style="width: ${task.progress || 0}%"></div>
                    </div>
                    <span class="progress-text">${Math.round(task.progress || 0)}%</span>
                </div>
                ${task.speed || task.eta ? `
                    <div class="queue-item-details">
                        ${task.speed ? `<span>Speed: ${task.speed}</span>` : ''}
                        ${task.eta ? `<span>ETA: ${task.eta}</span>` : ''}
                    </div>
                ` : ''}
                <div class="queue-item-actions">
                    ${task.status === 'completed' ? `
                        <a href="${api.getDownloadURL(task.task_id)}" class="btn btn-small btn-primary" download>
                            ⬇️ Download File
                        </a>
                    ` : ''}
                    ${['queued', 'downloading', 'fetching_info'].includes(task.status) ? `
                        <button class="btn btn-small btn-secondary" onclick="app.cancelTask('${task.task_id}')">
                            ❌ Cancel
                        </button>
                    ` : ''}
                    ${['completed', 'failed', 'cancelled'].includes(task.status) ? `
                        <button class="btn btn-small btn-secondary" onclick="app.removeTask('${task.task_id}')">
                            🗑️ Remove
                        </button>
                    ` : ''}
                </div>
                ${task.error ? `<p class="queue-item-error" style="color: var(--error-color); font-size: 0.8rem; margin-top: 8px;">Error: ${task.error}</p>` : ''}
            `;
            this.queueContainer.appendChild(item);
        });
    }

    async cancelTask(taskId) {
        try {
            await api.cancelDownload(taskId);
            this.showToast('Download cancelled', 'info');
            this.refreshQueue();
        } catch (error) {
            this.showToast(`Failed to cancel: ${error.message}`, 'error');
        }
    }

    async removeTask(taskId) {
        try {
            await api.removeDownload(taskId);
            this.refreshQueue();
        } catch (error) {
            this.showToast(`Failed to remove: ${error.message}`, 'error');
        }
    }

    // Utility methods
    formatDate(dateStr) {
        if (!dateStr || dateStr.length !== 8) return dateStr;
        const year = dateStr.substring(0, 4);
        const month = dateStr.substring(4, 6);
        const day = dateStr.substring(6, 8);
        return `${year}-${month}-${day}`;
    }

    formatFilesize(bytes) {
        if (!bytes) return 'Unknown';
        if (bytes >= 1073741824) return `${(bytes / 1073741824).toFixed(2)} GB`;
        if (bytes >= 1048576) return `${(bytes / 1048576).toFixed(2)} MB`;
        if (bytes >= 1024) return `${(bytes / 1024).toFixed(2)} KB`;
        return `${bytes} B`;
    }

    formatStatus(status) {
        const statusMap = {
            'queued': 'Queued',
            'fetching_info': 'Fetching Info',
            'downloading': 'Downloading',
            'processing': 'Processing',
            'completed': 'Completed',
            'failed': 'Failed',
            'cancelled': 'Cancelled'
        };
        return statusMap[status] || status;
    }

    showLoading(show) {
        if (show) {
            this.loadingOverlay.classList.remove('hidden');
        } else {
            this.loadingOverlay.classList.add('hidden');
        }
    }

    showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.innerHTML = `
            <span>${type === 'success' ? '✅' : type === 'error' ? '❌' : 'ℹ️'}</span>
            <span>${message}</span>
        `;

        this.toastContainer.appendChild(toast);

        setTimeout(() => {
            toast.style.opacity = '0';
            setTimeout(() => toast.remove(), 300);
        }, 4000);
    }
}

// Initialize app
const app = new App();
