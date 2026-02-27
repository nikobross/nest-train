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
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                ...options
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
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
        return `${API_BASE_URL}/images/${filename}`;
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
    async updateProgress(currentIndex) {
        return this.request('/progress', {
            method: 'POST',
            body: JSON.stringify({ current_index: currentIndex })
        });
    }

    /**
     * Get annotation for specific image
     */
    async getAnnotation(imageIndex) {
        return this.request(`/annotations/${imageIndex}`);
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

    /**
     * Export all annotations
     */
    async exportAnnotations() {
        return this.request('/annotations/export');
    }
}

// Create singleton instance
const api = new APIClient();
