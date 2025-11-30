/**
 * YouTube Downloader - Simplified App
 * Clean, fast, mobile-first UX
 */

class App {
    constructor() {
        // State
        this.currentVideo = null;
        this.currentTaskId = null;
        this.settings = this.loadSettings();
        this.history = this.loadHistory();
        
        // Options
        this.selectedFormat = 'video';
        this.selectedQuality = 'best';
        
        // Debounce timer for auto-fetch
        this.fetchDebounce = null;
        
        // Initialize
        this.init();
    }

    init() {
        this.bindElements();
        this.bindEvents();
        this.applyTheme(this.settings.theme);
        this.checkAPIStatus();
        this.renderHistory();
        this.setupClipboardDetection();
        this.autoFocusInput();
    }

    // ==================== Settings & Storage ====================

    loadSettings() {
        try {
            const saved = localStorage.getItem('yt-dl-settings');
            return saved ? JSON.parse(saved) : {
                theme: 'dark',
                defaultQuality: 'best',
                autoPaste: true,
                saveHistory: true
            };
        } catch {
            return { theme: 'dark', defaultQuality: 'best', autoPaste: true, saveHistory: true };
        }
    }

    saveSettings() {
        localStorage.setItem('yt-dl-settings', JSON.stringify(this.settings));
    }

    loadHistory() {
        try {
            const saved = localStorage.getItem('yt-dl-history');
            return saved ? JSON.parse(saved) : [];
        } catch {
            return [];
        }
    }

    saveHistory() {
        // Keep only last 10 items
        this.history = this.history.slice(0, 10);
        localStorage.setItem('yt-dl-history', JSON.stringify(this.history));
    }

    addToHistory(video) {
        if (!this.settings.saveHistory) return;
        
        // Remove duplicate if exists
        this.history = this.history.filter(h => h.url !== video.url);
        
        // Add new item at the start
        this.history.unshift({
            url: video.url,
            title: video.title,
            thumbnail: video.thumbnail,
            duration: video.duration,
            format: this.selectedFormat,
            quality: this.selectedQuality,
            timestamp: Date.now()
        });
        
        this.saveHistory();
        this.renderHistory();
    }

    clearHistory() {
        this.history = [];
        this.saveHistory();
        this.renderHistory();
        this.showToast('History cleared', 'success');
    }

    // ==================== Element Bindings ====================

    bindElements() {
        // Input
        this.urlInput = document.getElementById('url-input');
        this.pasteBtn = document.getElementById('paste-btn');
        this.clearBtn = document.getElementById('clear-btn');
        this.clipboardBanner = document.getElementById('clipboard-banner');
        this.useClipboardBtn = document.getElementById('use-clipboard-btn');
        
        // Preview
        this.previewSection = document.getElementById('preview-section');
        this.thumbnail = document.getElementById('thumbnail');
        this.duration = document.getElementById('duration');
        this.videoTitle = document.getElementById('video-title');
        this.channelName = document.getElementById('channel-name');
        this.viewCount = document.getElementById('view-count');
        this.uploadDate = document.getElementById('upload-date');
        
        // Download buttons
        this.downloadButtons = document.getElementById('download-buttons');
        this.downloadMp4Btn = document.getElementById('download-mp4');
        this.downloadMp3Btn = document.getElementById('download-mp3');
        this.moreOptionsBtn = document.getElementById('more-options-btn');
        
        // Advanced panel
        this.advancedPanel = document.getElementById('advanced-panel');
        this.closeAdvancedBtn = document.getElementById('close-advanced');
        this.formatTabs = document.querySelectorAll('.format-tab');
        this.qualityGroup = document.getElementById('quality-group');
        this.audioQualityGroup = document.getElementById('audio-quality-group');
        this.qualityBtns = document.querySelectorAll('#quality-grid .quality-btn');
        this.audioQualityBtns = document.querySelectorAll('#audio-quality-grid .quality-btn');
        this.subtitleSelect = document.getElementById('subtitle-select');
        this.embedSubtitles = document.getElementById('embed-subtitles');
        this.advancedDownloadBtn = document.getElementById('advanced-download-btn');
        
        // Status
        this.statusSection = document.getElementById('status-section');
        this.statusTitle = document.getElementById('status-title');
        this.statusMessage = document.getElementById('status-message');
        this.progressContainer = document.getElementById('progress-container');
        this.progressFill = document.getElementById('progress-fill');
        this.progressPercent = document.getElementById('progress-percent');
        this.progressEta = document.getElementById('progress-eta');
        this.cancelBtn = document.getElementById('cancel-btn');
        
        // Ready
        this.readySection = document.getElementById('ready-section');
        this.readyFilename = document.getElementById('ready-filename');
        this.readyFilesize = document.getElementById('ready-filesize');
        this.downloadLink = document.getElementById('download-link');
        this.retryBtn = document.getElementById('retry-download-btn');
        this.qrShareBtn = document.getElementById('qr-share-btn');
        
        // History
        this.historySection = document.getElementById('history-section');
        this.historyList = document.getElementById('history-list');
        this.clearHistoryBtn = document.getElementById('clear-history-btn');
        
        // Mobile bar
        this.mobileBar = document.getElementById('mobile-bar');
        this.mobileBarTitle = document.getElementById('mobile-bar-title');
        this.mobileDownloadBtn = document.getElementById('mobile-download-btn');
        
        // Footer
        this.statusDot = document.getElementById('status-dot');
        this.statusText = document.getElementById('status-text');
        this.settingsBtn = document.getElementById('settings-btn');
        
        // Theme
        this.themeToggle = document.getElementById('theme-toggle');
        
        // Modals
        this.errorModal = document.getElementById('error-modal');
        this.errorTitle = document.getElementById('error-title');
        this.errorMessage = document.getElementById('error-message');
        this.errorRetryBtn = document.getElementById('error-retry-btn');
        
        this.qrModal = document.getElementById('qr-modal');
        this.qrCode = document.getElementById('qr-code');
        this.qrUrl = document.getElementById('qr-url');
        this.copyUrlBtn = document.getElementById('copy-url-btn');
        
        this.settingsModal = document.getElementById('settings-modal');
        this.defaultQualitySelect = document.getElementById('default-quality');
        this.autoPasteCheckbox = document.getElementById('auto-paste');
        this.saveHistoryCheckbox = document.getElementById('save-history');
        this.themeBtns = document.querySelectorAll('.theme-btn');
        
        // Toast
        this.toastContainer = document.getElementById('toast-container');
    }

    bindEvents() {
        // URL Input
        this.urlInput.addEventListener('input', () => this.handleUrlInput());
        this.urlInput.addEventListener('paste', () => setTimeout(() => this.handleUrlInput(), 50));
        this.pasteBtn.addEventListener('click', () => this.pasteFromClipboard());
        this.clearBtn.addEventListener('click', () => this.clearInput());
        
        // Clipboard banner
        this.useClipboardBtn?.addEventListener('click', () => this.useClipboardUrl());
        
        // Download buttons
        this.downloadMp4Btn.addEventListener('click', () => this.downloadVideo('video', 'best'));
        this.downloadMp3Btn.addEventListener('click', () => this.downloadVideo('audio', '320kbps'));
        this.moreOptionsBtn.addEventListener('click', () => this.showAdvancedPanel());
        
        // Advanced panel
        this.closeAdvancedBtn.addEventListener('click', () => this.hideAdvancedPanel());
        this.formatTabs.forEach(tab => {
            tab.addEventListener('click', () => this.selectFormat(tab.dataset.format));
        });
        this.qualityBtns.forEach(btn => {
            btn.addEventListener('click', () => this.selectQuality(btn.dataset.quality, 'video'));
        });
        this.audioQualityBtns.forEach(btn => {
            btn.addEventListener('click', () => this.selectQuality(btn.dataset.quality, 'audio'));
        });
        this.advancedDownloadBtn.addEventListener('click', () => this.downloadWithOptions());
        
        // Cancel
        this.cancelBtn.addEventListener('click', () => this.cancelDownload());
        
        // Ready section
        this.retryBtn.addEventListener('click', () => this.retryDownload());
        this.qrShareBtn.addEventListener('click', () => this.showQRModal());
        
        // History
        this.clearHistoryBtn.addEventListener('click', () => this.clearHistory());
        
        // Mobile bar
        this.mobileDownloadBtn.addEventListener('click', () => this.downloadVideo('video', 'best'));
        
        // Theme toggle
        this.themeToggle.addEventListener('click', () => this.toggleTheme());
        
        // Settings
        this.settingsBtn.addEventListener('click', () => this.openSettingsModal());
        this.themeBtns.forEach(btn => {
            btn.addEventListener('click', () => this.setTheme(btn.dataset.theme));
        });
        this.defaultQualitySelect?.addEventListener('change', () => this.updateSettings());
        this.autoPasteCheckbox?.addEventListener('change', () => this.updateSettings());
        this.saveHistoryCheckbox?.addEventListener('change', () => this.updateSettings());
        
        // Error modal
        this.errorRetryBtn.addEventListener('click', () => {
            this.closeErrorModal();
            this.handleUrlInput();
        });
        
        // Copy URL
        this.copyUrlBtn?.addEventListener('click', () => this.copyDownloadUrl());
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.hideAdvancedPanel();
                this.closeErrorModal();
                this.closeQRModal();
                this.closeSettingsModal();
            }
        });
    }

    // ==================== URL Input & Auto-Fetch ====================

    handleUrlInput() {
        const url = this.urlInput.value.trim();
        
        // Show/hide clear button
        this.clearBtn.classList.toggle('hidden', !url);
        
        // Clear previous debounce
        if (this.fetchDebounce) {
            clearTimeout(this.fetchDebounce);
        }
        
        // Validate YouTube URL
        if (!this.isValidYouTubeUrl(url)) {
            if (!url) {
                this.resetUI();
            }
            return;
        }
        
        // Auto-fetch with debounce (300ms)
        this.fetchDebounce = setTimeout(() => {
            this.fetchVideoInfo(url);
        }, 300);
    }

    isValidYouTubeUrl(url) {
        const patterns = [
            /^(https?:\/\/)?(www\.)?(youtube\.com|youtu\.be)\/.+/i,
            /^(https?:\/\/)?(www\.)?youtube\.com\/watch\?v=[\w-]+/i,
            /^(https?:\/\/)?youtu\.be\/[\w-]+/i,
            /^(https?:\/\/)?(www\.)?youtube\.com\/shorts\/[\w-]+/i
        ];
        return patterns.some(p => p.test(url));
    }

    async fetchVideoInfo(url) {
        try {
            // Show loading state
            this.showStatus('Processing...', 'Fetching video information');
            
            const response = await api.getVideoInfo(url);
            
            if (response.error) {
                throw new Error(response.error);
            }
            
            this.currentVideo = {
                url: url,
                title: response.title,
                thumbnail: response.thumbnail,
                duration: response.duration,
                channel: response.channel || response.uploader,
                views: response.view_count,
                uploadDate: response.upload_date,
                formats: response.formats || [],
                subtitles: response.subtitles || {}
            };
            
            this.showPreview();
            this.hideStatus();
            this.populateSubtitles();
            
        } catch (error) {
            this.hideStatus();
            this.showFriendlyError(error);
        }
    }

    showPreview() {
        if (!this.currentVideo) return;
        
        // Set thumbnail
        this.thumbnail.src = this.currentVideo.thumbnail || '';
        this.thumbnail.alt = this.currentVideo.title;
        
        // Set duration
        this.duration.textContent = this.formatDuration(this.currentVideo.duration);
        
        // Set video info
        this.videoTitle.textContent = this.currentVideo.title;
        this.channelName.textContent = this.currentVideo.channel || 'Unknown channel';
        this.viewCount.textContent = this.formatViews(this.currentVideo.views);
        this.uploadDate.textContent = this.formatDate(this.currentVideo.uploadDate);
        
        // Show sections
        this.previewSection.classList.remove('hidden');
        this.downloadButtons.classList.remove('hidden');
        
        // Show mobile bar
        this.mobileBarTitle.textContent = this.truncateText(this.currentVideo.title, 30);
        this.mobileBar.classList.remove('hidden');
    }

    populateSubtitles() {
        if (!this.currentVideo?.subtitles) return;
        
        this.subtitleSelect.innerHTML = '<option value="">No subtitles</option>';
        
        const subtitles = this.currentVideo.subtitles;
        Object.keys(subtitles).forEach(lang => {
            const option = document.createElement('option');
            option.value = lang;
            option.textContent = this.getLanguageName(lang);
            this.subtitleSelect.appendChild(option);
        });
    }

    getLanguageName(code) {
        const languages = {
            'en': 'English',
            'es': 'Spanish',
            'fr': 'French',
            'de': 'German',
            'pt': 'Portuguese',
            'ru': 'Russian',
            'ja': 'Japanese',
            'ko': 'Korean',
            'zh': 'Chinese',
            'ar': 'Arabic',
            'hi': 'Hindi',
            'it': 'Italian'
        };
        return languages[code] || code.toUpperCase();
    }

    clearInput() {
        this.urlInput.value = '';
        this.clearBtn.classList.add('hidden');
        this.resetUI();
    }

    resetUI() {
        this.currentVideo = null;
        this.previewSection.classList.add('hidden');
        this.downloadButtons.classList.add('hidden');
        this.advancedPanel.classList.add('hidden');
        this.statusSection.classList.add('hidden');
        this.readySection.classList.add('hidden');
        this.mobileBar.classList.add('hidden');
    }

    // ==================== Clipboard Detection ====================

    setupClipboardDetection() {
        if (!this.settings.autoPaste) return;
        
        // Check clipboard on focus
        window.addEventListener('focus', () => this.checkClipboard());
        
        // Initial check
        setTimeout(() => this.checkClipboard(), 500);
    }

    async checkClipboard() {
        if (!this.settings.autoPaste) return;
        if (this.urlInput.value.trim()) return; // Don't override existing input
        
        try {
            const text = await navigator.clipboard.readText();
            if (this.isValidYouTubeUrl(text)) {
                this.clipboardUrl = text;
                this.clipboardBanner.classList.remove('hidden');
            }
        } catch {
            // Clipboard access denied or not supported
        }
    }

    useClipboardUrl() {
        if (this.clipboardUrl) {
            this.urlInput.value = this.clipboardUrl;
            this.clipboardBanner.classList.add('hidden');
            this.handleUrlInput();
        }
    }

    async pasteFromClipboard() {
        try {
            const text = await navigator.clipboard.readText();
            this.urlInput.value = text;
            this.handleUrlInput();
        } catch {
            this.showToast('Unable to access clipboard', 'error');
        }
    }

    autoFocusInput() {
        // Auto-focus on desktop, not on mobile (to prevent keyboard popup)
        if (window.innerWidth > 768) {
            this.urlInput.focus();
        }
    }

    // ==================== Advanced Panel ====================

    showAdvancedPanel() {
        this.advancedPanel.classList.remove('hidden');
        this.downloadButtons.classList.add('hidden');
    }

    hideAdvancedPanel() {
        this.advancedPanel.classList.add('hidden');
        if (this.currentVideo) {
            this.downloadButtons.classList.remove('hidden');
        }
    }

    selectFormat(format) {
        this.selectedFormat = format;
        
        // Update tabs
        this.formatTabs.forEach(tab => {
            tab.classList.toggle('active', tab.dataset.format === format);
        });
        
        // Show/hide quality groups
        this.qualityGroup.classList.toggle('hidden', format === 'audio');
        this.audioQualityGroup.classList.toggle('hidden', format !== 'audio');
    }

    selectQuality(quality, type) {
        this.selectedQuality = quality;
        
        const buttons = type === 'audio' ? this.audioQualityBtns : this.qualityBtns;
        buttons.forEach(btn => {
            btn.classList.toggle('active', btn.dataset.quality === quality);
        });
    }

    // ==================== Download ====================

    async downloadVideo(format, quality) {
        if (!this.currentVideo) return;
        
        this.selectedFormat = format;
        this.selectedQuality = quality;
        
        try {
            // Show status
            this.showStatus('Preparing Download', 'This may take a few moments...');
            this.hideAdvancedPanel();
            this.downloadButtons.classList.add('hidden');
            
            // Start download
            const params = {
                url: this.currentVideo.url,
                format: format,
                quality: quality
            };
            
            // Add subtitles if selected
            const subtitleLang = this.subtitleSelect?.value;
            if (subtitleLang && format === 'video') {
                params.subtitle_lang = subtitleLang;
                params.embed_subs = this.embedSubtitles?.checked || false;
            }
            
            const response = await api.startDownload(params);
            
            if (response.error) {
                throw new Error(response.error);
            }
            
            this.currentTaskId = response.task_id;
            
            // Poll for progress
            this.pollDownloadProgress();
            
        } catch (error) {
            this.hideStatus();
            this.downloadButtons.classList.remove('hidden');
            this.showFriendlyError(error);
        }
    }

    downloadWithOptions() {
        this.downloadVideo(this.selectedFormat, this.selectedQuality);
    }

    async pollDownloadProgress() {
        if (!this.currentTaskId) return;
        
        try {
            const response = await api.getTaskStatus(this.currentTaskId);
            
            if (response.status === 'completed') {
                this.downloadComplete(response);
                return;
            }
            
            if (response.status === 'error' || response.status === 'failed') {
                throw new Error(response.error || 'Download failed');
            }
            
            // Update progress
            if (response.progress !== undefined) {
                this.showProgress(response.progress, response.speed, response.eta);
            }
            
            // Continue polling
            setTimeout(() => this.pollDownloadProgress(), 1000);
            
        } catch (error) {
            this.hideStatus();
            this.downloadButtons.classList.remove('hidden');
            this.showFriendlyError(error);
        }
    }

    downloadComplete(response) {
        this.hideStatus();
        
        // Add to history
        this.addToHistory(this.currentVideo);
        
        // Show ready section
        this.readyFilename.textContent = response.filename || 'video.mp4';
        this.readyFilesize.textContent = this.formatFileSize(response.filesize);
        this.downloadLink.href = response.download_url || `/api/download/${this.currentTaskId}`;
        this.downloadLink.download = response.filename || 'video.mp4';
        
        // Store for QR
        this.currentDownloadUrl = response.download_url || `${window.location.origin}/api/download/${this.currentTaskId}`;
        
        this.readySection.classList.remove('hidden');
        this.mobileBar.classList.add('hidden');
        
        this.showToast('Your download is ready!', 'success');
    }

    async cancelDownload() {
        if (this.currentTaskId) {
            try {
                await api.cancelTask(this.currentTaskId);
            } catch {
                // Ignore cancel errors
            }
        }
        
        this.currentTaskId = null;
        this.hideStatus();
        this.downloadButtons.classList.remove('hidden');
        this.showToast('Download cancelled', 'info');
    }

    retryDownload() {
        this.readySection.classList.add('hidden');
        this.downloadButtons.classList.remove('hidden');
        this.mobileBar.classList.remove('hidden');
    }

    // ==================== Status & Progress ====================

    showStatus(title, message) {
        this.statusTitle.textContent = title;
        this.statusMessage.textContent = message;
        this.progressContainer.classList.add('hidden');
        this.statusSection.classList.remove('hidden');
        this.readySection.classList.add('hidden');
    }

    showProgress(percent, speed, eta) {
        this.statusTitle.textContent = 'Downloading...';
        this.statusMessage.textContent = '';
        this.progressContainer.classList.remove('hidden');
        
        this.progressFill.style.width = `${percent}%`;
        this.progressPercent.textContent = `${Math.round(percent)}%`;
        this.progressEta.textContent = eta ? `${eta} remaining` : 'Estimating...';
        
        if (speed) {
            this.statusMessage.textContent = speed;
        }
    }

    hideStatus() {
        this.statusSection.classList.add('hidden');
    }

    // ==================== Error Handling ====================

    showFriendlyError(error) {
        const message = error.message || error;
        
        // Map to friendly messages
        const friendlyMessages = {
            'Video unavailable': 'Unable to fetch video. Maybe the link is private or age-restricted.',
            'Private video': 'This video is private and cannot be downloaded.',
            'age-restricted': 'This video is age-restricted. Try logging in.',
            'copyright': 'This video is not available due to copyright restrictions.',
            'not available': 'This format is not available for this video.',
            'rate limit': 'Your download is throttled. Try again in a few seconds.',
            'network': 'Slow connection — check your internet and retry.',
            'timeout': 'Request timed out. Please try again.',
            'Failed to fetch': 'Unable to connect to server. Please check your connection.'
        };
        
        let friendlyMessage = 'Something went wrong. Please try again.';
        for (const [key, friendly] of Object.entries(friendlyMessages)) {
            if (message.toLowerCase().includes(key.toLowerCase())) {
                friendlyMessage = friendly;
                break;
            }
        }
        
        this.errorTitle.textContent = 'Oops!';
        this.errorMessage.textContent = friendlyMessage;
        this.errorModal.classList.remove('hidden');
    }

    closeErrorModal() {
        this.errorModal.classList.add('hidden');
    }

    // ==================== QR Code ====================

    showQRModal() {
        if (!this.currentDownloadUrl) return;
        
        // Clear previous QR
        this.qrCode.innerHTML = '';
        
        // Generate QR code
        if (typeof QRCode !== 'undefined') {
            QRCode.toCanvas(this.qrCode, this.currentDownloadUrl, {
                width: 200,
                margin: 2,
                color: { dark: '#000', light: '#fff' }
            }, (error) => {
                if (error) console.error(error);
            });
        }
        
        this.qrUrl.value = this.currentDownloadUrl;
        this.qrModal.classList.remove('hidden');
    }

    closeQRModal() {
        this.qrModal.classList.add('hidden');
    }

    async copyDownloadUrl() {
        try {
            await navigator.clipboard.writeText(this.currentDownloadUrl);
            this.showToast('URL copied to clipboard', 'success');
        } catch {
            this.showToast('Failed to copy URL', 'error');
        }
    }

    // ==================== History ====================

    renderHistory() {
        if (!this.history.length) {
            this.historyList.innerHTML = `
                <div class="history-empty">
                    <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                        <circle cx="12" cy="12" r="10"/>
                        <polyline points="12 6 12 12 16 14"/>
                    </svg>
                    <p>No downloads yet</p>
                </div>
            `;
            this.clearHistoryBtn.classList.add('hidden');
            return;
        }
        
        this.clearHistoryBtn.classList.remove('hidden');
        
        this.historyList.innerHTML = this.history.map((item, index) => `
            <div class="history-item" data-index="${index}">
                <img class="history-thumb" src="${item.thumbnail || ''}" alt="${item.title}">
                <div class="history-info">
                    <div class="history-title">${this.truncateText(item.title, 40)}</div>
                    <div class="history-meta">${item.format?.toUpperCase() || 'MP4'} • ${this.formatTimeAgo(item.timestamp)}</div>
                </div>
                <button class="history-download-btn" onclick="app.redownloadFromHistory(${index})">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                        <polyline points="7 10 12 15 17 10"/>
                        <line x1="12" y1="15" x2="12" y2="3"/>
                    </svg>
                </button>
            </div>
        `).join('');
    }

    redownloadFromHistory(index) {
        const item = this.history[index];
        if (!item) return;
        
        this.urlInput.value = item.url;
        this.handleUrlInput();
    }

    // ==================== Settings ====================

    openSettingsModal() {
        // Populate settings
        if (this.defaultQualitySelect) {
            this.defaultQualitySelect.value = this.settings.defaultQuality;
        }
        if (this.autoPasteCheckbox) {
            this.autoPasteCheckbox.checked = this.settings.autoPaste;
        }
        if (this.saveHistoryCheckbox) {
            this.saveHistoryCheckbox.checked = this.settings.saveHistory;
        }
        
        // Update theme buttons
        this.themeBtns.forEach(btn => {
            btn.classList.toggle('active', btn.dataset.theme === this.settings.theme);
        });
        
        this.settingsModal.classList.remove('hidden');
    }

    closeSettingsModal() {
        this.settingsModal.classList.add('hidden');
    }

    updateSettings() {
        this.settings.defaultQuality = this.defaultQualitySelect?.value || 'best';
        this.settings.autoPaste = this.autoPasteCheckbox?.checked ?? true;
        this.settings.saveHistory = this.saveHistoryCheckbox?.checked ?? true;
        this.saveSettings();
    }

    // ==================== Theme ====================

    toggleTheme() {
        const newTheme = this.settings.theme === 'dark' ? 'light' : 'dark';
        this.setTheme(newTheme);
    }

    setTheme(theme) {
        this.settings.theme = theme;
        this.saveSettings();
        this.applyTheme(theme);
        
        // Update theme buttons in settings
        this.themeBtns.forEach(btn => {
            btn.classList.toggle('active', btn.dataset.theme === theme);
        });
    }

    applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        
        // Update theme toggle icon
        const sunIcon = this.themeToggle?.querySelector('.icon-sun');
        const moonIcon = this.themeToggle?.querySelector('.icon-moon');
        
        if (theme === 'dark') {
            sunIcon?.classList.remove('hidden');
            moonIcon?.classList.add('hidden');
        } else {
            sunIcon?.classList.add('hidden');
            moonIcon?.classList.remove('hidden');
        }
    }

    // ==================== API Status ====================

    async checkAPIStatus() {
        try {
            const response = await api.checkHealth();
            const isOnline = response && (response.status === 'healthy' || response.status === 'ok');
            
            this.statusDot.classList.toggle('online', isOnline);
            this.statusDot.classList.toggle('offline', !isOnline);
            this.statusText.textContent = isOnline ? 'Online' : 'Offline';
        } catch {
            this.statusDot.classList.add('offline');
            this.statusText.textContent = 'Offline';
        }
        
        // Check again in 30 seconds
        setTimeout(() => this.checkAPIStatus(), 30000);
    }

    // ==================== Toast ====================

    showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.innerHTML = `
            <p>${message}</p>
        `;
        
        this.toastContainer.appendChild(toast);
        
        // Auto remove after 4 seconds
        setTimeout(() => {
            toast.style.animation = 'slideIn 0.3s ease reverse';
            setTimeout(() => toast.remove(), 300);
        }, 4000);
    }

    // ==================== Utilities ====================

    formatDuration(seconds) {
        if (!seconds) return '';
        const hrs = Math.floor(seconds / 3600);
        const mins = Math.floor((seconds % 3600) / 60);
        const secs = seconds % 60;
        
        if (hrs > 0) {
            return `${hrs}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
        }
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    }

    formatViews(count) {
        if (!count) return '';
        if (count >= 1000000) return `${(count / 1000000).toFixed(1)}M views`;
        if (count >= 1000) return `${(count / 1000).toFixed(1)}K views`;
        return `${count} views`;
    }

    formatDate(dateStr) {
        if (!dateStr) return '';
        try {
            // Handle YYYYMMDD format
            if (/^\d{8}$/.test(dateStr)) {
                const year = dateStr.slice(0, 4);
                const month = dateStr.slice(4, 6);
                const day = dateStr.slice(6, 8);
                return new Date(`${year}-${month}-${day}`).toLocaleDateString();
            }
            return new Date(dateStr).toLocaleDateString();
        } catch {
            return dateStr;
        }
    }

    formatFileSize(bytes) {
        if (!bytes) return 'Unknown size';
        const units = ['B', 'KB', 'MB', 'GB'];
        let i = 0;
        while (bytes >= 1024 && i < units.length - 1) {
            bytes /= 1024;
            i++;
        }
        return `${bytes.toFixed(1)} ${units[i]}`;
    }

    formatTimeAgo(timestamp) {
        const seconds = Math.floor((Date.now() - timestamp) / 1000);
        
        if (seconds < 60) return 'Just now';
        if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
        if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
        if (seconds < 604800) return `${Math.floor(seconds / 86400)}d ago`;
        return new Date(timestamp).toLocaleDateString();
    }

    truncateText(text, maxLength) {
        if (!text || text.length <= maxLength) return text;
        return text.slice(0, maxLength) + '...';
    }
}

// Initialize app when DOM is ready
let app;
document.addEventListener('DOMContentLoaded', () => {
    app = new App();
});

// Expose to window for onclick handlers
window.app = app;
