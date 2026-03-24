/**
 * API Client for communicating with the backend
 */

const API_BASE_URL = 'http://localhost:5001/api';

class APIClient {
    /**
     * Generic fetch wrapper with error handling
     */
    async request(endpoint, options = {}) {
        try {
            const response = await fetch(`${API_BASE_URL}${endpoint}`, {
                credentials: 'include',
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                ...options
            });
            const contentType = response.headers.get('content-type') || '';
            let payload = null;
            if (contentType.includes('application/json')) {
                payload = await response.json();
            } else {
                payload = { success: response.ok, data: await response.text() };
            }

            if (!response.ok) {
                const message = payload && payload.error ? payload.error : `HTTP error! status: ${response.status}`;
                throw new Error(message);
            }

            return payload;
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    }

    /**
     * Health check
     */
    async healthCheck() {
        return this.request('/health');
    }

    /**
     * Get list of all images
     */
    async getImageList() {
        return this.request('/images/list');
    }

    /**
     * Get image URL
     */
    getImageURL(filename) {
        if (filename.startsWith('http://') || filename.startsWith('https://')) {
            return filename;
        }
        return `${API_BASE_URL}/images/${filename}`;
    }

    /**
     * Start Google OAuth flow.
     */
    async startGoogleLogin() {
        const response = await this.request('/auth/google-login');
        if (!response.success || !response.auth_url) {
            throw new Error(response.error || 'Failed to start Google login');
        }
        return response.auth_url;
    }

    /**
     * Get session auth status.
     */
    async getAuthStatus() {
        return this.request('/auth/status');
    }

    /**
     * Logout current session.
     */
    async logout() {
        return this.request('/auth/logout', { method: 'POST' });
    }

    /**
     * Get sheet configuration for current session.
     */
    async getSheetConfig() {
        return this.request('/sheets/config');
    }

    /**
     * Set sheet URL/ID for current session.
     */
    async setSheetConfig(sheetInput) {
        return this.request('/sheets/config', {
            method: 'POST',
            body: JSON.stringify({ sheet_input: sheetInput })
        });
    }

    /**
     * Get pending sheet write queue size.
     */
    async getSheetQueueStatus() {
        return this.request('/sheets/queue-status');
    }

    /**
     * Flush pending sheet writes in batches.
     */
    async flushSheetQueue(maxItems = 100) {
        return this.request('/sheets/flush', {
            method: 'POST',
            body: JSON.stringify({ max_items: maxItems })
        });
    }

    /**
     * Get current progress
     */
    async getProgress() {
        return this.request('/progress');
    }

    /**
     * Update progress
     */
    async updateProgress(currentIndex, persistRemote = false) {
        return this.request('/progress', {
            method: 'POST',
            body: JSON.stringify({ current_index: currentIndex, persist_remote: persistRemote })
        });
    }

    /**
     * Get annotation for specific image
     */
    async getAnnotation(imageIndex, sheetRow = null) {
        const query = Number.isInteger(sheetRow) ? `?sheet_row=${sheetRow}` : '';
        return this.request(`/annotations/${imageIndex}${query}`);
    }

    /**
     * Save annotation for specific image
     */
    async saveAnnotation(imageIndex, annotationData) {
        return this.request(`/annotations/${imageIndex}`, {
            method: 'POST',
            body: JSON.stringify(annotationData)
        });
    }
}

// Create singleton instance
const api = new APIClient();
