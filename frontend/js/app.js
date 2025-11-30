/**
 * YouTube Downloader - Main Application
 * Phase 3: Mobile-first responsive UI
 */

class App {
    constructor() {
        this.currentVideoInfo = null;
        this.playlistItems = [];
        this.selectedPlaylistItems = new Set();
        this.activeTasks = new Map();
        this.pollInterval = null;
        
        // Settings
        this.currentFormat = 'video'; // video, audio, mobile
        this.currentQuality = '1080p';
        this.audioQualities = ['320kbps', '256kbps', '192kbps', '128kbps'];
        this.videoQualities = ['2160p', '1440p', '1080p', '720p', '480p', '360p'];
        this.mobileQualities = ['720p', '480p', '360p'];

        this.init();
    }

    init() {
        this.bindElements();
        this.bindEvents();
        this.checkAPIStatus();
        this.startQueuePolling();
        this.setupPasteFromClipboard();
    }

    bindElements() {
        // Input elements
        this.urlInput = document.getElementById('url-input');
        this.pasteBtn = document.getElementById('paste-btn');
        this.clearBtn = document.getElementById('clear-btn');
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
        this.videoDescription = document.getElementById('video-description');

        // Format selection
        this.formatSelection = document.getElementById('format-selection');
        this.formatTabs = document.querySelectorAll('.format-tab');
        this.qualityOptions = document.getElementById('quality-options');
        this.qualityGrid = document.getElementById('quality-grid');
        this.formatsList = document.getElementById('formats-list');

        // Playlist elements
        this.playlistSection = document.getElementById('playlist-section');
        this.playlistTitle = document.getElementById('playlist-title');
        this.playlistCount = document.getElementById('playlist-count');
        this.playlistContainer = document.getElementById('playlist-container');
        this.selectAllBtn = document.getElementById('select-all-btn');
        this.deselectAllBtn = document.getElementById('deselect-all-btn');
        this.selectedCount = document.getElementById('selected-count');

        // Queue elements
        this.queueSection = document.getElementById('queue-section');
        this.queueContainer = document.getElementById('queue-container');
        this.clearCompletedBtn = document.getElementById('clear-completed-btn');

        // Bottom bar
        this.bottomBar = document.getElementById('bottom-bar');
        this.bottomTitle = document.getElementById('bottom-title');
        this.bottomSize = document.getElementById('bottom-size');
        this.bottomDownloadBtn = document.getElementById('bottom-download-btn');

        // Status elements
        this.statusDot = document.getElementById('status-dot');
        this.apiStatusText = document.getElementById('api-status-text');

        // Modal elements
        this.downloadModal = document.getElementById('download-modal');
        this.modalFilename = document.getElementById('modal-filename');
        this.modalFilesize = document.getElementById('modal-filesize');
        this.modalDownloadBtn = document.getElementById('modal-download-btn');
        this.modalCloseBtn = document.getElementById('modal-close-btn');

        // Loading/Toast
        this.loadingOverlay = document.getElementById('loading-overlay');
        this.loadingText = document.getElementById('loading-text');
        this.toastContainer = document.getElementById('toast-container');
        
        // Offline banner
        this.offlineBanner = document.getElementById('offline-banner');

        // Install button
        this.installBtn = document.getElementById('install-btn');
    }

    bindEvents() {
        // URL input events
        this.urlInput?.addEventListener('input', () => this.handleUrlInput());
        this.urlInput?.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.handlePreview();
        });

        // Button clicks
        this.pasteBtn?.addEventListener('click', () => this.pasteFromClipboard());
        this.clearBtn?.addEventListener('click', () => this.clearUrl());
        this.previewBtn?.addEventListener('click', () => this.handlePreview());
        this.downloadBtn?.addEventListener('click', () => this.handleDownload());
        this.bottomDownloadBtn?.addEventListener('click', () => this.handleDownload());
        this.clearCompletedBtn?.addEventListener('click', () => this.handleClearCompleted());

        // Format tabs
        this.formatTabs?.forEach(tab => {
            tab.addEventListener('click', () => this.handleFormatTabClick(tab));
        });

        // Playlist controls
        this.selectAllBtn?.addEventListener('click', () => this.selectAllPlaylist());
        this.deselectAllBtn?.addEventListener('click', () => this.deselectAllPlaylist());

        // Modal
        this.modalCloseBtn?.addEventListener('click', () => this.closeModal());
        document.querySelector('.modal-backdrop')?.addEventListener('click', () => this.closeModal());

        // Install PWA
        this.installBtn?.addEventListener('click', () => this.installPWA());

        // Online/Offline events
        window.addEventListener('online', () => this.handleOnline());
        window.addEventListener('offline', () => this.handleOffline());
    }

    setupPasteFromClipboard() {
        // Auto-paste when app regains focus
        document.addEventListener('visibilitychange', () => {
            if (document.visibilityState === 'visible' && !this.urlInput?.value) {
                this.autoPasteFromClipboard();
            }
        });
    }

    async autoPasteFromClipboard() {
        try {
            const text = await navigator.clipboard.readText();
            if (this.isValidYouTubeUrl(text) && !this.urlInput.value) {
                this.urlInput.value = text;
                this.handleUrlInput();
            }
        } catch {
            // Clipboard access denied - ignore silently
        }
    }

    async pasteFromClipboard() {
        try {
            const text = await navigator.clipboard.readText();
            this.urlInput.value = text;
            this.handleUrlInput();
        } catch (error) {
            this.showToast('Unable to access clipboard', 'error');
        }
    }

    clearUrl() {
        this.urlInput.value = '';
        this.handleUrlInput();
        this.urlInput.focus();
    }

    handleUrlInput() {
        const hasValue = this.urlInput.value.trim().length > 0;
        this.clearBtn?.classList.toggle('hidden', !hasValue);
        this.pasteBtn?.classList.toggle('hidden', hasValue);
    }

    isValidYouTubeUrl(url) {
        const patterns = [
            /^(https?:\/\/)?(www\.)?(youtube\.com|youtu\.be)\/.+$/,
            /^(https?:\/\/)?(music\.youtube\.com)\/.+$/
        ];
        return patterns.some(pattern => pattern.test(url));
    }

    async checkAPIStatus() {
        try {
            const health = await api.checkHealth();
            this.statusDot?.classList.add('online');
            this.statusDot?.classList.remove('offline');
            if (this.apiStatusText) {
                this.apiStatusText.textContent = `API Online (yt-dlp ${health.yt_dlp_version || 'N/A'})`;
            }
        } catch (error) {
            this.statusDot?.classList.add('offline');
            this.statusDot?.classList.remove('online');
            if (this.apiStatusText) {
                this.apiStatusText.textContent = 'API Offline';
            }
        }
    }

    handleOnline() {
        this.offlineBanner?.classList.add('hidden');
        this.checkAPIStatus();
    }

    handleOffline() {
        this.offlineBanner?.classList.remove('hidden');
    }

    // Format tab handling
    handleFormatTabClick(tab) {
        const format = tab.dataset.format;
        this.currentFormat = format;

        // Update active state
        this.formatTabs.forEach(t => t.classList.remove('active'));
        tab.classList.add('active');

        // Update quality options
        this.renderQualityOptions();
    }

    renderQualityOptions() {
        if (!this.qualityGrid) return;

        let qualities;
        switch (this.currentFormat) {
            case 'audio':
                qualities = this.audioQualities;
                this.currentQuality = '320kbps';
                break;
            case 'mobile':
                qualities = this.mobileQualities;
                this.currentQuality = '720p';
                break;
            default:
                qualities = this.videoQualities;
                this.currentQuality = '1080p';
        }

        this.qualityGrid.innerHTML = qualities.map(q => `
            <button class="quality-btn ${q === this.currentQuality ? 'active' : ''}" data-quality="${q}">
                ${q}
            </button>
        `).join('');

        // Bind quality button events
        this.qualityGrid.querySelectorAll('.quality-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                this.qualityGrid.querySelectorAll('.quality-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                this.currentQuality = btn.dataset.quality;
                this.updateBottomBar();
            });
        });
    }

    async handlePreview() {
        const url = this.urlInput?.value.trim();
        if (!url) {
            this.showToast('Please enter a YouTube URL', 'error');
            return;
        }

        this.showLoading(true, 'Fetching video info...');
        if (this.previewBtn) this.previewBtn.disabled = true;

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

            this.previewSection?.classList.remove('hidden');
            this.formatSelection?.classList.remove('hidden');
            this.bottomBar?.classList.remove('hidden');

            // Render quality options
            this.renderQualityOptions();
            this.updateBottomBar();

        } catch (error) {
            this.showToast(`Failed to fetch video info: ${error.message}`, 'error');
        } finally {
            this.showLoading(false);
            if (this.previewBtn) this.previewBtn.disabled = false;
        }
    }

    displayVideoInfo(info) {
        if (this.thumbnail) {
            this.thumbnail.src = info.thumbnail || '';
            this.thumbnail.alt = info.title || 'Video thumbnail';
        }
        if (this.durationBadge) this.durationBadge.textContent = info.duration_formatted || '';
        if (this.videoTitle) this.videoTitle.textContent = info.title || 'Unknown Title';
        if (this.channelName) this.channelName.textContent = info.channel || 'Unknown Channel';
        if (this.viewCount) this.viewCount.textContent = info.view_count_formatted ? `${info.view_count_formatted} views` : '';
        if (this.uploadDate) this.uploadDate.textContent = info.upload_date ? this.formatDate(info.upload_date) : '';
        if (this.videoDescription) {
            this.videoDescription.textContent = info.description?.substring(0, 150) + '...' || '';
        }

        // Hide playlist section
        this.playlistSection?.classList.add('hidden');

        // Display formats in collapsible
        if (info.formats && info.formats.length > 0) {
            this.displayFormats(info.formats);
        }
    }

    displayPlaylistInfo(info) {
        if (this.videoTitle) this.videoTitle.textContent = info.title || 'Unknown Playlist';
        if (this.channelName) this.channelName.textContent = info.channel || '';
        if (this.thumbnail) {
            this.thumbnail.src = info.videos?.[0]?.thumbnail || '';
        }
        if (this.durationBadge) this.durationBadge.textContent = `${info.video_count} videos`;
        if (this.viewCount) this.viewCount.textContent = '';
        if (this.uploadDate) this.uploadDate.textContent = '';

        // Display playlist items
        this.playlistItems = info.videos || [];
        this.selectedPlaylistItems = new Set(this.playlistItems.map((_, i) => i));
        
        if (this.playlistTitle) this.playlistTitle.textContent = info.title || 'Playlist';
        if (this.playlistCount) this.playlistCount.textContent = `${this.playlistItems.length} videos`;

        this.renderPlaylistItems();
        this.updateSelectedCount();

        this.playlistSection?.classList.remove('hidden');
    }

    renderPlaylistItems() {
        if (!this.playlistContainer) return;

        this.playlistContainer.innerHTML = this.playlistItems.map((video, index) => `
            <div class="playlist-item">
                <input type="checkbox" 
                       class="playlist-checkbox" 
                       id="playlist-${index}" 
                       data-index="${index}"
                       ${this.selectedPlaylistItems.has(index) ? 'checked' : ''}>
                <span class="playlist-item-index">${index + 1}</span>
                <img class="playlist-item-thumb" 
                     src="${video.thumbnail || ''}" 
                     alt=""
                     onerror="this.src='data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 16 9%22><rect fill=%22%23333%22 width=%2216%22 height=%229%22/></svg>'">
                <div class="playlist-item-info">
                    <div class="playlist-item-title">${video.title || 'Unknown'}</div>
                    <div class="playlist-item-duration">${video.duration_formatted || ''}</div>
                </div>
            </div>
        `).join('');

        // Bind checkbox events
        this.playlistContainer.querySelectorAll('.playlist-checkbox').forEach(checkbox => {
            checkbox.addEventListener('change', (e) => {
                const index = parseInt(e.target.dataset.index);
                if (e.target.checked) {
                    this.selectedPlaylistItems.add(index);
                } else {
                    this.selectedPlaylistItems.delete(index);
                }
                this.updateSelectedCount();
            });
        });
    }

    updateSelectedCount() {
        if (this.selectedCount) {
            this.selectedCount.textContent = `${this.selectedPlaylistItems.size} selected`;
        }
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
        if (!this.formatsList) return;

        // Filter and sort formats
        const videoFormats = formats
            .filter(f => f.resolution && f.resolution !== 'audio only')
            .slice(0, 10);

        this.formatsList.innerHTML = videoFormats.map(f => `
            <div class="format-item">
                <div class="format-item-info">
                    <span class="format-item-resolution">${f.resolution || 'N/A'}</span>
                    <span class="format-item-ext">${f.extension || f.ext || ''}</span>
                </div>
                <span class="format-item-size">${this.formatFilesize(f.filesize || f.filesize_approx)}</span>
            </div>
        `).join('');
    }

    updateBottomBar() {
        if (!this.currentVideoInfo || !this.bottomBar) return;

        const title = this.currentVideoInfo.title || 'Video';
        if (this.bottomTitle) {
            this.bottomTitle.textContent = title.length > 40 ? title.substring(0, 40) + '...' : title;
        }
        if (this.bottomSize) {
            this.bottomSize.textContent = `${this.currentFormat.toUpperCase()} • ${this.currentQuality}`;
        }
    }

    async handleDownload() {
        const url = this.urlInput?.value.trim();
        if (!url) {
            this.showToast('Please enter a YouTube URL', 'error');
            return;
        }

        // Determine format settings
        const audioOnly = this.currentFormat === 'audio';
        const mobileOptimized = this.currentFormat === 'mobile';

        let quality = this.currentQuality.replace('p', '').replace('kbps', '');

        const downloadRequest = {
            url,
            format: audioOnly ? 'mp3' : 'mp4',
            quality: quality,
            audio_only: audioOnly,
        };

        // Add playlist items if applicable
        if (this.playlistItems.length > 0 && this.selectedPlaylistItems.size > 0) {
            downloadRequest.playlist_items = Array.from(this.selectedPlaylistItems).map(i => i + 1);
        }

        // Mobile compression endpoint
        if (mobileOptimized) {
            return this.handleMobileDownload(url, quality);
        }

        if (this.downloadBtn) this.downloadBtn.disabled = true;
        if (this.bottomDownloadBtn) this.bottomDownloadBtn.disabled = true;

        try {
            const response = await api.startDownload(downloadRequest);
            this.showToast(`Download started: ${this.currentVideoInfo?.title || 'Video'}`, 'success');
            this.activeTasks.set(response.task_id, response);
            this.refreshQueue();
            this.queueSection?.classList.remove('hidden');
        } catch (error) {
            this.showToast(`Failed to start download: ${error.message}`, 'error');
        } finally {
            if (this.downloadBtn) this.downloadBtn.disabled = false;
            if (this.bottomDownloadBtn) this.bottomDownloadBtn.disabled = false;
        }
    }

    async handleMobileDownload(url, quality) {
        try {
            this.showLoading(true, 'Preparing mobile-optimized download...');
            
            const response = await api.mobileCompression({
                url,
                audio_only: false,
                max_resolution: quality + 'p'
            });

            // Download the file directly
            api.downloadBlob(response.blob, response.filename);
            this.showToast(`Download complete: ${response.filename}`, 'success');
        } catch (error) {
            this.showToast(`Failed to start mobile download: ${error.message}`, 'error');
        } finally {
            this.showLoading(false);
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
            this.renderQueue(status.tasks || []);
        } catch (error) {
            console.error('Failed to refresh queue:', error);
        }
    }

    renderQueue(tasks) {
        if (!this.queueContainer) return;

        if (!tasks || tasks.length === 0) {
            this.queueContainer.innerHTML = `
                <div class="queue-empty">
                    <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                        <polyline points="7,10 12,15 17,10"></polyline>
                        <line x1="12" y1="15" x2="12" y2="3"></line>
                    </svg>
                    <p>No downloads in queue</p>
                    <span>Enter a URL above to get started</span>
                </div>
            `;
            return;
        }

        this.queueContainer.innerHTML = tasks.map(task => `
            <div class="queue-item ${task.status}">
                <div class="queue-item-icon">
                    ${this.getStatusIcon(task.status)}
                </div>
                <div class="queue-item-info">
                    <div class="queue-item-title">${task.title || task.task_id}</div>
                    <div class="queue-item-status">
                        ${task.status === 'downloading' ? `
                            <div class="queue-item-progress">
                                <div class="queue-item-progress-bar" style="width: ${task.progress || 0}%"></div>
                            </div>
                            <span>${Math.round(task.progress || 0)}%</span>
                            ${task.speed ? `<span>• ${task.speed}</span>` : ''}
                        ` : `
                            <span>${this.formatStatus(task.status)}</span>
                        `}
                    </div>
                </div>
                <div class="queue-item-actions">
                    ${task.status === 'completed' ? `
                        <a href="${api.getDownloadURL(task.task_id)}" class="queue-item-btn" download title="Download">
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                                <polyline points="7,10 12,15 17,10"></polyline>
                                <line x1="12" y1="15" x2="12" y2="3"></line>
                            </svg>
                        </a>
                    ` : ''}
                    ${['queued', 'downloading', 'fetching_info'].includes(task.status) ? `
                        <button class="queue-item-btn" onclick="app.cancelTask('${task.task_id}')" title="Cancel">
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <line x1="18" y1="6" x2="6" y2="18"></line>
                                <line x1="6" y1="6" x2="18" y2="18"></line>
                            </svg>
                        </button>
                    ` : ''}
                    ${['completed', 'failed', 'cancelled'].includes(task.status) ? `
                        <button class="queue-item-btn" onclick="app.removeTask('${task.task_id}')" title="Remove">
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <polyline points="3,6 5,6 21,6"></polyline>
                                <path d="M19,6v14a2,2,0,0,1-2,2H7a2,2,0,0,1-2-2V6m3,0V4a2,2,0,0,1,2-2h4a2,2,0,0,1,2,2v2"></path>
                            </svg>
                        </button>
                    ` : ''}
                </div>
            </div>
        `).join('');
    }

    getStatusIcon(status) {
        const icons = {
            'queued': `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><polyline points="12,6 12,12 16,14"></polyline></svg>`,
            'fetching_info': `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12" y2="8"></line></svg>`,
            'downloading': `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7,10 12,15 17,10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>`,
            'processing': `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="2" x2="12" y2="6"></line><line x1="12" y1="18" x2="12" y2="22"></line><line x1="4.93" y1="4.93" x2="7.76" y2="7.76"></line><line x1="16.24" y1="16.24" x2="19.07" y2="19.07"></line><line x1="2" y1="12" x2="6" y2="12"></line><line x1="18" y1="12" x2="22" y2="12"></line><line x1="4.93" y1="19.07" x2="7.76" y2="16.24"></line><line x1="16.24" y1="7.76" x2="19.07" y2="4.93"></line></svg>`,
            'completed': `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22,4 12,14.01 9,11.01"></polyline></svg>`,
            'failed': `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg>`,
            'cancelled': `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="8" y1="12" x2="16" y2="12"></line></svg>`
        };
        return icons[status] || icons['queued'];
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

    // Modal methods
    showDownloadModal(filename, filesize, downloadUrl) {
        if (this.modalFilename) this.modalFilename.textContent = filename;
        if (this.modalFilesize) this.modalFilesize.textContent = filesize;
        if (this.modalDownloadBtn) {
            this.modalDownloadBtn.href = downloadUrl;
            this.modalDownloadBtn.download = filename;
        }
        this.downloadModal?.classList.remove('hidden');
    }

    closeModal() {
        this.downloadModal?.classList.add('hidden');
    }

    // PWA Install
    installPWA() {
        if (window.deferredPrompt) {
            window.deferredPrompt.prompt();
            window.deferredPrompt.userChoice.then(result => {
                if (result.outcome === 'accepted') {
                    this.showToast('App installed successfully!', 'success');
                }
                window.deferredPrompt = null;
            });
        }
    }

    // Utility methods
    formatDate(dateStr) {
        if (!dateStr || dateStr.length !== 8) return dateStr;
        const year = dateStr.substring(0, 4);
        const month = dateStr.substring(4, 6);
        const day = dateStr.substring(6, 8);
        const date = new Date(year, month - 1, day);
        return date.toLocaleDateString(undefined, { 
            year: 'numeric', 
            month: 'short', 
            day: 'numeric' 
        });
    }

    formatFilesize(bytes) {
        if (!bytes) return 'Unknown';
        if (bytes >= 1073741824) return `${(bytes / 1073741824).toFixed(1)} GB`;
        if (bytes >= 1048576) return `${(bytes / 1048576).toFixed(1)} MB`;
        if (bytes >= 1024) return `${(bytes / 1024).toFixed(1)} KB`;
        return `${bytes} B`;
    }

    formatStatus(status) {
        const statusMap = {
            'queued': 'Queued',
            'fetching_info': 'Fetching Info...',
            'downloading': 'Downloading',
            'processing': 'Processing...',
            'completed': 'Completed',
            'failed': 'Failed',
            'cancelled': 'Cancelled'
        };
        return statusMap[status] || status;
    }

    showLoading(show, text = 'Loading...') {
        if (show) {
            if (this.loadingText) this.loadingText.textContent = text;
            this.loadingOverlay?.classList.remove('hidden');
        } else {
            this.loadingOverlay?.classList.add('hidden');
        }
    }

    showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        
        const icons = {
            success: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#00c853" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22,4 12,14.01 9,11.01"></polyline></svg>`,
            error: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#ff5252" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg>`,
            warning: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#ffab00" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>`,
            info: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#448aff" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>`
        };

        toast.innerHTML = `
            <div class="toast-icon">${icons[type] || icons.info}</div>
            <div class="toast-content">
                <div class="toast-message">${message}</div>
            </div>
            <button class="toast-close" onclick="this.parentElement.remove()">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <line x1="18" y1="6" x2="6" y2="18"></line>
                    <line x1="6" y1="6" x2="18" y2="18"></line>
                </svg>
            </button>
        `;

        this.toastContainer?.appendChild(toast);

        // Auto remove after 5 seconds
        setTimeout(() => {
            toast.classList.add('toast-exit');
            setTimeout(() => toast.remove(), 300);
        }, 5000);
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.app = new App();
});

// PWA Install prompt handler
window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    window.deferredPrompt = e;
    // Show install button
    const installBtn = document.getElementById('install-btn');
    if (installBtn) installBtn.classList.remove('hidden');
});
