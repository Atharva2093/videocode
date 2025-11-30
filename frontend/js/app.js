/**
 * YouTube Downloader - Main Application
 * Phase 3-5: Mobile-first responsive UI + Mobile Optimization
 * Phase 7-10: UI Polish, Settings, Search, Progress
 */

class App {
    constructor() {
        this.currentVideoInfo = null;
        this.playlistItems = [];
        this.selectedPlaylistItems = new Set();
        this.activeTasks = new Map();
        this.pollInterval = null;
        this.currentDownloadTaskId = null;
        
        // Input mode
        this.inputMode = 'url'; // 'url' or 'search'
        
        // Settings (loaded from localStorage)
        this.settings = this.loadSettings();
        
        // Settings
        this.currentFormat = this.settings.defaultFormat || 'video'; // video, audio, mobile
        this.currentQuality = this.settings.defaultQuality || '1080p';
        this.currentMobilePreset = 'auto'; // auto, mobile-video, mobile-audio
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
        this.applyTheme(this.settings.theme || 'dark');
        this.applySettings();
    }

    loadSettings() {
        try {
            const saved = localStorage.getItem('yt-downloader-settings');
            return saved ? JSON.parse(saved) : {
                theme: 'dark',
                defaultFormat: 'video',
                defaultQuality: '1080p',
                showMobilePresets: true,
                enableQRSharing: true,
                autoDownload: false
            };
        } catch {
            return {
                theme: 'dark',
                defaultFormat: 'video',
                defaultQuality: '1080p',
                showMobilePresets: true,
                enableQRSharing: true,
                autoDownload: false
            };
        }
    }

    saveSettings() {
        const formatSelect = document.getElementById('settings-format');
        const qualitySelect = document.getElementById('settings-quality');
        const mobilePresetsCheckbox = document.getElementById('settings-mobile-presets');
        const qrSharingCheckbox = document.getElementById('settings-qr-sharing');
        const autoDownloadCheckbox = document.getElementById('settings-auto-download');

        this.settings = {
            ...this.settings,
            defaultFormat: formatSelect?.value || 'video',
            defaultQuality: qualitySelect?.value || '1080p',
            showMobilePresets: mobilePresetsCheckbox?.checked ?? true,
            enableQRSharing: qrSharingCheckbox?.checked ?? true,
            autoDownload: autoDownloadCheckbox?.checked ?? false
        };

        localStorage.setItem('yt-downloader-settings', JSON.stringify(this.settings));
        this.showToast('Settings saved', 'success');
    }

    applySettings() {
        // Apply settings to UI
        const formatSelect = document.getElementById('settings-format');
        const qualitySelect = document.getElementById('settings-quality');
        const mobilePresetsCheckbox = document.getElementById('settings-mobile-presets');
        const qrSharingCheckbox = document.getElementById('settings-qr-sharing');
        const autoDownloadCheckbox = document.getElementById('settings-auto-download');

        if (formatSelect) formatSelect.value = this.settings.defaultFormat;
        if (qualitySelect) qualitySelect.value = this.settings.defaultQuality;
        if (mobilePresetsCheckbox) mobilePresetsCheckbox.checked = this.settings.showMobilePresets;
        if (qrSharingCheckbox) qrSharingCheckbox.checked = this.settings.enableQRSharing;
        if (autoDownloadCheckbox) autoDownloadCheckbox.checked = this.settings.autoDownload;

        // Apply theme buttons
        document.querySelectorAll('.settings-toggle-btn[data-theme]').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.theme === this.settings.theme);
        });
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
        
        // Mobile presets
        this.mobilePresets = document.getElementById('mobile-presets');
        this.presetBtns = document.querySelectorAll('.preset-btn');

        // QR Code modal
        this.qrModal = document.getElementById('qr-modal');
        this.qrCodeContainer = document.getElementById('qr-code');
        this.qrUrlInput = document.getElementById('qr-url-input');

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
        
        // Progress overlay
        this.progressOverlay = document.getElementById('progress-overlay');
        this.progressTitle = document.getElementById('progress-title');
        this.progressSubtitle = document.getElementById('progress-subtitle');
        this.progressBar = document.getElementById('progress-bar-fill');
        this.progressPercent = document.getElementById('progress-percent');
        this.progressSpeed = document.getElementById('progress-speed');
        this.progressEta = document.getElementById('progress-eta');
        this.progressCancelBtn = document.getElementById('progress-cancel-btn');
        
        // Complete modal
        this.completeModal = document.getElementById('complete-modal');
        this.completeFilename = document.getElementById('complete-filename');
        this.completeFilesize = document.getElementById('complete-filesize');
        this.completeDownloadLink = document.getElementById('complete-download-link');
        
        // Settings modal
        this.settingsModal = document.getElementById('settings-modal');
        
        // Search results
        this.searchResults = document.getElementById('search-results');
        
        // Offline banner
        this.offlineBanner = document.getElementById('offline-banner');

        // Install button
        this.installBtn = document.getElementById('install-btn');
        
        // Subtitle elements
        this.subtitleSection = document.getElementById('subtitle-section');
        this.subtitleSelect = document.getElementById('subtitle-select');
        this.subtitleMerge = document.getElementById('subtitle-merge');
    }

    bindEvents() {
        // URL input events
        this.urlInput?.addEventListener('input', () => this.handleUrlInput());
        this.urlInput?.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                if (this.inputMode === 'search') {
                    this.handleSearch();
                } else {
                    this.handlePreview();
                }
            }
        });

        // Button clicks
        this.pasteBtn?.addEventListener('click', () => this.pasteFromClipboard());
        this.clearBtn?.addEventListener('click', () => this.clearUrl());
        this.previewBtn?.addEventListener('click', () => this.handlePreview());
        this.downloadBtn?.addEventListener('click', () => this.handleDownload());
        this.bottomDownloadBtn?.addEventListener('click', () => this.handleDownload());
        this.clearCompletedBtn?.addEventListener('click', () => this.handleClearCompleted());
        
        // Progress cancel button
        this.progressCancelBtn?.addEventListener('click', () => this.cancelCurrentDownload());

        // Format tabs
        this.formatTabs?.forEach(tab => {
            tab.addEventListener('click', () => this.handleFormatTabClick(tab));
        });

        // Mobile preset buttons
        document.querySelectorAll('.preset-btn')?.forEach(btn => {
            btn.addEventListener('click', () => this.handlePresetClick(btn));
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
        
        // Metadata button
        document.getElementById('metadata-btn')?.addEventListener('click', () => {
            if (this.inputMode === 'search') {
                this.handleSearch();
            } else {
                this.handlePreview();
            }
        });
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

        // Show/hide mobile presets vs quality options
        if (format === 'mobile') {
            this.mobilePresets?.classList.remove('hidden');
            this.qualityOptions?.classList.add('hidden');
        } else {
            this.mobilePresets?.classList.add('hidden');
            this.qualityOptions?.classList.remove('hidden');
            // Update quality options
            this.renderQualityOptions();
        }
    }

    // Mobile preset handling
    handlePresetClick(btn) {
        const preset = btn.dataset.preset;
        this.currentMobilePreset = preset;

        // Update active state
        document.querySelectorAll('.preset-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');

        this.updateBottomBar();
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

        // Mobile compression endpoint with presets
        if (mobileOptimized) {
            return this.handleMobileDownload(url);
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

    async handleMobileDownload(url) {
        try {
            this.showLoading(true, 'Preparing mobile-optimized download...');
            
            let options = { url };
            
            // Apply preset settings
            switch (this.currentMobilePreset) {
                case 'mobile-video':
                    options.max_resolution = '480p';
                    options.audio_only = false;
                    break;
                case 'mobile-audio':
                    options.audio_only = true;
                    options.max_resolution = '480p'; // Not used for audio
                    break;
                case 'auto':
                default:
                    // Auto-detect best settings based on device
                    const isMobile = window.innerWidth < 768;
                    options.max_resolution = isMobile ? '480p' : '720p';
                    options.audio_only = false;
                    break;
            }
            
            const response = await api.mobileCompression(options);

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
                        <button class="queue-item-btn" onclick="app.showShareOption('${task.task_id}', '${(task.title || 'video').replace(/'/g, "\\'")}')" title="Share QR Code">
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <rect x="3" y="3" width="7" height="7"></rect>
                                <rect x="14" y="3" width="7" height="7"></rect>
                                <rect x="3" y="14" width="7" height="7"></rect>
                                <rect x="14" y="14" width="3" height="3"></rect>
                                <rect x="18" y="14" width="3" height="3"></rect>
                                <rect x="14" y="18" width="3" height="3"></rect>
                                <rect x="18" y="18" width="3" height="3"></rect>
                            </svg>
                        </button>
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

    // ==========================================
    // Theme Methods
    // ==========================================
    
    setTheme(theme) {
        this.settings.theme = theme;
        localStorage.setItem('yt-downloader-settings', JSON.stringify(this.settings));
        this.applyTheme(theme);
        
        // Update theme toggle buttons
        document.querySelectorAll('.settings-toggle-btn[data-theme]').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.theme === theme);
        });
    }
    
    applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        
        // Update theme icons in header
        const darkIcon = document.getElementById('theme-icon-dark');
        const lightIcon = document.getElementById('theme-icon-light');
        
        if (theme === 'light') {
            darkIcon?.classList.add('hidden');
            lightIcon?.classList.remove('hidden');
        } else {
            darkIcon?.classList.remove('hidden');
            lightIcon?.classList.add('hidden');
        }
    }
    
    toggleTheme() {
        const newTheme = this.settings.theme === 'dark' ? 'light' : 'dark';
        this.setTheme(newTheme);
    }

    // ==========================================
    // Settings Modal Methods
    // ==========================================
    
    openSettingsModal() {
        this.applySettings();
        this.settingsModal?.classList.remove('hidden');
    }
    
    closeSettingsModal() {
        this.settingsModal?.classList.add('hidden');
    }

    // ==========================================
    // Input Mode Methods (URL/Search)
    // ==========================================
    
    setInputMode(mode) {
        this.inputMode = mode;
        
        // Update toggle buttons
        document.querySelectorAll('.input-mode-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.mode === mode);
        });
        
        // Update input placeholder and type
        if (this.urlInput) {
            if (mode === 'search') {
                this.urlInput.placeholder = 'Search YouTube videos...';
                this.urlInput.type = 'text';
                this.urlInput.inputMode = 'text';
            } else {
                this.urlInput.placeholder = 'Paste YouTube URL here...';
                this.urlInput.type = 'url';
                this.urlInput.inputMode = 'url';
            }
        }
        
        // Update metadata button text
        const metadataBtn = document.getElementById('metadata-btn');
        if (metadataBtn) {
            const span = metadataBtn.querySelector('span');
            if (span) {
                span.textContent = mode === 'search' ? 'Search' : 'Get Info';
            }
        }
        
        // Hide search results when switching to URL mode
        if (mode === 'url') {
            this.searchResults?.classList.add('hidden');
        }
    }
    
    async handleSearch() {
        const query = this.urlInput?.value.trim();
        if (!query) {
            this.showToast('Please enter a search term', 'error');
            return;
        }
        
        this.searchResults?.classList.remove('hidden');
        this.searchResults.innerHTML = `
            <div class="search-loading">
                <div class="loading-spinner"></div>
                <p>Searching YouTube...</p>
            </div>
        `;
        
        try {
            const results = await api.searchYouTube(query);
            this.displaySearchResults(results);
        } catch (error) {
            this.searchResults.innerHTML = `
                <div class="search-loading">
                    <p style="color: var(--color-error);">Search failed: ${error.message}</p>
                </div>
            `;
        }
    }
    
    displaySearchResults(results) {
        if (!results || results.length === 0) {
            this.searchResults.innerHTML = `
                <div class="search-loading">
                    <p>No results found</p>
                </div>
            `;
            return;
        }
        
        this.searchResults.innerHTML = results.map(video => `
            <div class="search-result-item" onclick="app.selectSearchResult('${video.url}')">
                <img class="search-result-thumb" src="${video.thumbnail || ''}" alt="" 
                     onerror="this.src='data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 16 9%22><rect fill=%22%23333%22 width=%2216%22 height=%229%22/></svg>'">
                <div class="search-result-info">
                    <div class="search-result-title">${video.title || 'Unknown'}</div>
                    <div class="search-result-channel">${video.channel || ''}</div>
                    <div class="search-result-meta">
                        ${video.duration_formatted || ''} ${video.view_count_formatted ? '• ' + video.view_count_formatted + ' views' : ''}
                    </div>
                </div>
            </div>
        `).join('');
    }
    
    selectSearchResult(url) {
        this.urlInput.value = url;
        this.searchResults?.classList.add('hidden');
        this.setInputMode('url');
        this.handlePreview();
    }

    // ==========================================
    // Progress Overlay Methods
    // ==========================================
    
    showProgressOverlay(title = 'Preparing Download', subtitle = 'Fetching video information...') {
        if (this.progressTitle) this.progressTitle.textContent = title;
        if (this.progressSubtitle) this.progressSubtitle.textContent = subtitle;
        if (this.progressBar) this.progressBar.style.width = '0%';
        if (this.progressPercent) this.progressPercent.textContent = '0%';
        if (this.progressSpeed) this.progressSpeed.textContent = '';
        if (this.progressEta) this.progressEta.textContent = '';
        
        const icon = document.getElementById('progress-icon');
        icon?.classList.remove('success');
        
        this.progressOverlay?.classList.remove('hidden');
    }
    
    updateProgress(percent, speed = '', eta = '') {
        if (this.progressBar) this.progressBar.style.width = `${percent}%`;
        if (this.progressPercent) this.progressPercent.textContent = `${Math.round(percent)}%`;
        if (this.progressSpeed) this.progressSpeed.textContent = speed;
        if (this.progressEta) this.progressEta.textContent = eta ? `ETA: ${eta}` : '';
        
        if (percent >= 100) {
            if (this.progressTitle) this.progressTitle.textContent = 'Processing...';
            if (this.progressSubtitle) this.progressSubtitle.textContent = 'Finalizing your download...';
        }
    }
    
    hideProgressOverlay() {
        this.progressOverlay?.classList.add('hidden');
    }
    
    async cancelCurrentDownload() {
        if (this.currentDownloadTaskId) {
            try {
                await api.cancelDownload(this.currentDownloadTaskId);
                this.showToast('Download cancelled', 'info');
            } catch (error) {
                console.error('Failed to cancel:', error);
            }
        }
        this.hideProgressOverlay();
        this.currentDownloadTaskId = null;
    }

    // ==========================================
    // Complete Modal Methods
    // ==========================================
    
    showCompleteModal(filename, filesize, downloadUrl) {
        if (this.completeFilename) this.completeFilename.textContent = filename;
        if (this.completeFilesize) this.completeFilesize.textContent = filesize;
        if (this.completeDownloadLink) {
            this.completeDownloadLink.href = downloadUrl;
            this.completeDownloadLink.download = filename;
        }
        
        // Store for QR sharing
        this._lastCompletedDownload = { filename, filesize, downloadUrl };
        
        this.completeModal?.classList.remove('hidden');
        
        // Auto-download if enabled
        if (this.settings.autoDownload) {
            this.completeDownloadLink?.click();
        }
    }
    
    closeCompleteModal() {
        this.completeModal?.classList.add('hidden');
    }
    
    shareCompletedDownload() {
        if (this._lastCompletedDownload && this.settings.enableQRSharing) {
            const absoluteUrl = new URL(this._lastCompletedDownload.downloadUrl, window.location.origin).href;
            this.showQRCode(absoluteUrl, this._lastCompletedDownload.filename);
            this.closeCompleteModal();
        }
    }

    // ==========================================
    // Batch Download Methods
    // ==========================================
    
    async startBatchDownload() {
        if (this.selectedPlaylistItems.size === 0) {
            this.showToast('Please select at least one video', 'error');
            return;
        }
        
        this.showProgressOverlay('Batch Download', `Downloading ${this.selectedPlaylistItems.size} videos...`);
        
        const selectedIndices = Array.from(this.selectedPlaylistItems);
        let completed = 0;
        
        for (const index of selectedIndices) {
            const video = this.playlistItems[index];
            if (!video) continue;
            
            try {
                if (this.progressSubtitle) {
                    this.progressSubtitle.textContent = `Downloading: ${video.title || 'Video ' + (index + 1)}`;
                }
                
                const downloadRequest = {
                    url: video.url || video.webpage_url,
                    format: this.currentFormat === 'audio' ? 'mp3' : 'mp4',
                    quality: this.currentQuality.replace('p', '').replace('kbps', ''),
                    audio_only: this.currentFormat === 'audio',
                };
                
                await api.startDownload(downloadRequest);
                completed++;
                
                const progress = (completed / selectedIndices.length) * 100;
                this.updateProgress(progress);
                
            } catch (error) {
                console.error(`Failed to download video ${index}:`, error);
            }
        }
        
        this.hideProgressOverlay();
        this.showToast(`Added ${completed} videos to download queue`, 'success');
        this.refreshQueue();
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

    // ==========================================
    // QR Code Sharing Methods
    // ==========================================
    
    showQRCode(downloadUrl, filename) {
        if (!this.qrModal || !this.qrCodeContainer) return;

        // Clear previous QR code
        this.qrCodeContainer.innerHTML = '';
        
        // Set URL input
        if (this.qrUrlInput) {
            this.qrUrlInput.value = downloadUrl;
        }

        // Generate QR code using the library
        if (typeof QRCode !== 'undefined') {
            QRCode.toCanvas(downloadUrl, {
                width: 200,
                margin: 2,
                color: {
                    dark: '#000000',
                    light: '#ffffff'
                }
            }, (error, canvas) => {
                if (error) {
                    console.error('QR Code generation failed:', error);
                    this.qrCodeContainer.innerHTML = '<p style="color: var(--color-error);">Failed to generate QR code</p>';
                    return;
                }
                this.qrCodeContainer.appendChild(canvas);
            });
        } else {
            // Fallback if library not loaded
            this.qrCodeContainer.innerHTML = `
                <p style="color: var(--color-text-secondary); font-size: 0.875rem;">
                    QR code library not loaded.<br>
                    Copy the URL below instead.
                </p>
            `;
        }

        // Show modal
        this.qrModal.classList.remove('hidden');
    }

    closeQRModal() {
        this.qrModal?.classList.add('hidden');
    }

    async copyDownloadURL() {
        const url = this.qrUrlInput?.value;
        if (!url) return;

        try {
            await navigator.clipboard.writeText(url);
            this.showToast('URL copied to clipboard', 'success');
        } catch (error) {
            this.showToast('Failed to copy URL', 'error');
        }
    }

    // Call this when a download completes to show QR option
    showShareOption(taskId, filename) {
        const downloadUrl = api.getDownloadURL(taskId);
        
        // Create absolute URL
        const absoluteUrl = new URL(downloadUrl, window.location.origin).href;
        
        this.showQRCode(absoluteUrl, filename);
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
