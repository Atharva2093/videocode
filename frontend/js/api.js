/**
 * API Client for YouTube Downloader
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

    // Health endpoints
    async checkHealth() {
        return this.request('/health');
    }

    async ping() {
        return this.request('/ping');
    }

    // Video info endpoints
    async getVideoInfo(url) {
        return this.request('/info', {
            method: 'POST',
            body: JSON.stringify({ url }),
        });
    }

    async getFormats(videoId) {
        return this.request(`/formats/${videoId}`);
    }

    // Download endpoints
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
}

// Export singleton instance
const api = new APIClient();
