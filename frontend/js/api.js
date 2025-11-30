/**
 * API Client for YouTube Downloader - Phase 2
 * Supports: metadata, playlist, thumbnail, download, convert, mobile-compression
 */

const API_BASE_URL = 'http://localhost:8000/api';

class APIClient {
    constructor(baseURL = API_BASE_URL) {
        this.baseURL = baseURL;
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers,
            },
            ...options,
        };

        try {
            const response = await fetch(url, config);
            
            if (!response.ok) {
                const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
                throw new Error(error.detail || `HTTP ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            if (error.name === 'TypeError' && error.message === 'Failed to fetch') {
                throw new Error('Unable to connect to API server. Please ensure the backend is running.');
            }
            throw error;
        }
    }

    // ============== Health Endpoints ==============
    async checkHealth() {
        return this.request('/health');
    }

    async ping() {
        return this.request('/ping');
    }

    // ============== Phase 2: Metadata Endpoint ==============
    /**
     * GET /metadata - Get comprehensive video metadata
     * @param {string} url - YouTube video URL
     * @returns {Object} Video metadata including title, duration, formats, sizes
     */
    async getMetadata(url) {
        const encodedUrl = encodeURIComponent(url);
        return this.request(`/metadata?url=${encodedUrl}`);
    }

    // ============== Phase 2: Playlist Endpoint ==============
    /**
     * GET /playlist - Get playlist information
     * @param {string} url - YouTube playlist URL
     * @returns {Object} Playlist metadata with all video titles and IDs
     */
    async getPlaylist(url) {
        const encodedUrl = encodeURIComponent(url);
        return this.request(`/playlist?url=${encodedUrl}`);
    }

    // ============== Phase 2: Thumbnail Endpoint ==============
    /**
     * GET /thumbnail - Get video thumbnail URL
     * @param {string} url - YouTube video URL
     * @param {string} quality - Thumbnail quality (sd, mq, hq, maxres)
     * @returns {string} Direct URL to thumbnail image
     */
    getThumbnailURL(url, quality = 'hq') {
        const encodedUrl = encodeURIComponent(url);
        return `${this.baseURL}/thumbnail?url=${encodedUrl}&quality=${quality}`;
    }

    // ============== Legacy Video Info (Backward Compatibility) ==============
    async getVideoInfo(url) {
        return this.request('/info', {
            method: 'POST',
            body: JSON.stringify({ url }),
        });
    }

    async getFormats(videoId) {
        return this.request(`/formats/${videoId}`);
    }

    // ============== Queue-Based Download Endpoints ==============
    /**
     * POST /download - Start async download (queue-based)
     * @param {Object} downloadRequest - Download configuration
     * @returns {Object} Task ID and status
     */
    async startDownload(downloadRequest) {
        return this.request('/download', {
            method: 'POST',
            body: JSON.stringify(downloadRequest),
        });
    }

    async getDownloadStatus(taskId) {
        return this.request(`/download/${taskId}`);
    }

    async cancelDownload(taskId) {
        return this.request('/download/cancel', {
            method: 'POST',
            body: JSON.stringify({ task_id: taskId }),
        });
    }

    async removeDownload(taskId) {
        return this.request(`/download/${taskId}`, {
            method: 'DELETE',
        });
    }

    async getQueueStatus() {
        return this.request('/queue');
    }

    async clearCompleted() {
        return this.request('/queue/clear', {
            method: 'DELETE',
        });
    }

    getDownloadURL(taskId) {
        return `${this.baseURL}/download/${taskId}/file`;
    }

    // ============== Phase 2: Direct Download ==============
    /**
     * POST /download/direct - Synchronous download (returns file directly)
     * @param {Object} options - Download options
     * @param {string} options.url - YouTube URL
     * @param {string} options.quality - Video quality (1080p, 720p, etc.)
     * @param {string} options.format - Output format (mp4, webm)
     * @param {boolean} options.audio_only - Download audio only
     * @returns {Blob} Downloaded file
     */
    async directDownload({ url, quality = 'best', format = 'mp4', audio_only = false }) {
        const response = await fetch(`${this.baseURL}/download/direct`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ url, quality, format, audio_only }),
        });

        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: 'Download failed' }));
            throw new Error(error.detail);
        }

        const blob = await response.blob();
        const filename = this._extractFilename(response.headers);
        return { blob, filename };
    }

    // ============== Phase 2: Convert Endpoint ==============
    /**
     * POST /convert - Download and convert to specified format
     * @param {Object} options - Conversion options
     * @param {string} options.url - YouTube URL
     * @param {string} options.output_format - Target format (mp3, mp4, webm)
     * @param {string} options.video_quality - Video quality
     * @param {string} options.audio_quality - Audio quality (low, medium, high, very_high)
     * @param {boolean} options.compress - Enable compression
     * @returns {Blob} Converted file
     */
    async convert({ url, output_format, video_quality, audio_quality = 'high', compress = false }) {
        const response = await fetch(`${this.baseURL}/convert`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                url,
                output_format,
                video_quality,
                audio_quality,
                compress
            }),
        });

        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: 'Conversion failed' }));
            throw new Error(error.detail);
        }

        const blob = await response.blob();
        const filename = this._extractFilename(response.headers);
        return { blob, filename };
    }

    // ============== Phase 2: Mobile Compression ==============
    /**
     * POST /mobile-compression - Download with mobile-optimized settings
     * @param {Object} options - Mobile compression options
     * @param {string} options.url - YouTube URL
     * @param {boolean} options.audio_only - Audio only (64kbps MP3)
     * @param {string} options.max_resolution - Max resolution (default: 480p)
     * @returns {Blob} Compressed file
     */
    async mobileCompression({ url, audio_only = false, max_resolution = '480p' }) {
        const response = await fetch(`${this.baseURL}/mobile-compression`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                url,
                audio_only,
                max_resolution
            }),
        });

        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: 'Compression failed' }));
            throw new Error(error.detail);
        }

        const blob = await response.blob();
        const filename = this._extractFilename(response.headers);
        const fileSizeMB = response.headers.get('X-File-Size-MB');
        return { blob, filename, fileSizeMB };
    }

    // ============== Helper Methods ==============
    _extractFilename(headers) {
        const contentDisposition = headers.get('Content-Disposition');
        if (contentDisposition) {
            const match = contentDisposition.match(/filename="?([^";\n]+)"?/);
            if (match) return match[1];
        }
        return 'download';
    }

    /**
     * Helper to trigger file download in browser
     * @param {Blob} blob - File blob
     * @param {string} filename - Filename to save as
     */
    downloadBlob(blob, filename) {
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    /**
     * Smart info fetch - auto-detects video vs playlist
     * @param {string} url - YouTube URL
     * @returns {Object} Video or playlist metadata
     */
    async getSmartInfo(url) {
        const isPlaylist = url.includes('list=') || url.includes('/playlist?');
        if (isPlaylist) {
            return this.getPlaylist(url);
        }
        return this.getMetadata(url);
    }
}

// Export singleton instance
const api = new APIClient();
