/**
 * Main Application Logic
 */

class AnnotationApp {
    constructor() {
        this.images = [];
        this.currentIndex = 0;
        this.canvasManager = null;
        this.currentLabel = null;
        this.isInitialized = false;
        this.isAuthenticated = false;
        this.sheetConnected = false;
        this.pendingSheetWrites = 0;
        this.flushIntervalId = null;
        
        this.setupPostMessageListener();
        this.initializeElements();
        this.setupEventListeners();
        this.init();
    }

    /**
     * Listen for OAuth callback success.
     * Refresh auth state when callback completes.
     */
    setupPostMessageListener() {
        window.addEventListener('message', async (event) => {
            // Only accept messages from same origin (browser security)
            if (event.data && event.data.type === 'google-auth-success') {
                console.log('✓ Received auth success from callback');
                
                // Refresh auth state to confirm login
                await this.refreshAuthState();
                if (this.isAuthenticated) {
                    this.setStatus('Google login successful. Ready to annotate.', 'success');
                }
            }
        });
    }

    /**
     * Initialize DOM element references
     */
    initializeElements() {
        // Image elements
        this.imageContainer = document.getElementById('image-container');
        this.currentImage = document.getElementById('current-image');
        this.canvasOverlay = document.getElementById('canvas-overlay');
        
        // Info display
        this.currentIndexElem = document.getElementById('current-index');
        this.currentFilenameElem = document.getElementById('current-filename');
        this.currentRowElem = document.getElementById('current-row');
        this.currentColElem = document.getElementById('current-col');
        this.progressText = document.getElementById('progress-text');
        this.statusMessage = document.getElementById('status-message');
        this.boxCount = document.getElementById('box-count');
        this.boxesContainer = document.getElementById('boxes-container');
        
        // Buttons
        this.prevBtn = document.getElementById('prev-btn');
        this.nextBtn = document.getElementById('next-btn');
        this.hasPlasticBtn = document.getElementById('has-plastic-btn');
        this.noPlasticBtn = document.getElementById('no-plastic-btn');
        this.clearAllBoxesBtn = document.getElementById('clear-all-boxes');
        this.exportBtn = document.getElementById('export-btn');
        this.jumpBtn = document.getElementById('jump-btn');
        this.startBtn = document.getElementById('start-btn');

        // Auth controls
        this.authStatusElem = document.getElementById('auth-status');
        this.googleLoginBtn = document.getElementById('google-login-btn');
        this.googleLogoutBtn = document.getElementById('google-logout-btn');
        this.sheetUrlInput = document.getElementById('sheet-url-input');
        this.connectSheetBtn = document.getElementById('connect-sheet-btn');
        
        // Inputs
        this.jumpIndex = document.getElementById('jump-index');
        this.startIndex = document.getElementById('start-index');
    }

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Navigation
        this.prevBtn.addEventListener('click', () => this.previousImage());
        this.nextBtn.addEventListener('click', () => this.nextImage());
        this.jumpBtn.addEventListener('click', () => this.jumpToIndex());
        this.startBtn.addEventListener('click', () => this.startAnnotation());
        
        // Classification
        this.hasPlasticBtn.addEventListener('click', () => this.markAsHasPlastic());
        this.noPlasticBtn.addEventListener('click', () => this.markAsNoPlastic());
        this.clearAllBoxesBtn.addEventListener('click', () => this.clearAllBoxes());

        // Auth
        this.googleLoginBtn.addEventListener('click', () => this.loginWithGoogle());
        this.googleLogoutBtn.addEventListener('click', () => this.logoutGoogle());
        this.connectSheetBtn.addEventListener('click', () => this.connectSheet());
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => this.handleKeyboard(e));

        // Attempt a final flush on tab close/navigation.
        window.addEventListener('beforeunload', () => {
            if (this.isAuthenticated && this.sheetConnected && this.pendingSheetWrites > 0) {
                // Fire-and-forget; browser may not await completion.
                api.flushSheetQueue(200).catch(() => {});
            }
        });
        
        // Image load
        this.currentImage.addEventListener('load', () => this.onImageLoaded());
    }

    /**
     * Initialize the application
     */
    async init() {
        this.setStatus('Initializing...', 'info');
        
        try {
            // Health check
            await api.healthCheck();
            console.log('✓ Backend connection successful');

            // Restore auth state
            await this.refreshAuthState();

            if (this.isAuthenticated) {
                await this.loadSheetConfig();
            }

            this.updateProgress();
            if (this.isAuthenticated) {
                this.setStatus('Authenticated. Add a sheet URL and connect.', 'info');
            } else {
                this.setStatus('Sign in with Google to start annotation.', 'info');
            }
            
        } catch (error) {
            this.setStatus('Failed to connect to server. Please ensure the backend is running on port 5001.', 'error');
            console.error('Initialization error:', error);
        }
    }

    /**
     * Start annotation from specified index
     */
    async startAnnotation() {
        if (!this.isAuthenticated || !this.sheetConnected) {
            this.setStatus('Sign in and connect a Google Sheet first.', 'error');
            return;
        }

        const inputValue = this.startIndex.value.trim();
        const parsedIndex = inputValue === '' ? this.currentIndex : parseInt(inputValue, 10);
        const startIdx = Number.isNaN(parsedIndex) ? this.currentIndex : parsedIndex;

        if (this.images.length === 0) {
            this.setStatus('No images found in sheet list column.', 'error');
            return;
        }

        if (startIdx < 0 || startIdx >= this.images.length) {
            this.setStatus(`Invalid start index. Must be between 0 and ${this.images.length - 1}`, 'error');
            return;
        }

        this.currentIndex = startIdx;
        await this.loadImage(this.currentIndex);
        this.isInitialized = true;
        this.enableControls();
        this.setStatus('Annotation started.', 'success');
    }

    /**
     * Load and display image at specified index
     */
    async loadImage(index) {
        if (index < 0 || index >= this.images.length) {
            this.setStatus('Invalid image index', 'error');
            return;
        }
        
        // Save current annotation before changing image
        if (this.isInitialized && index !== this.currentIndex) {
            await this.saveCurrentAnnotation();
        }
        
        this.currentIndex = index;
        this.currentLabel = null;
        const imageData = this.images[index];
        
        console.log('Loading image:', imageData);
        
        // Update info display
        this.currentIndexElem.textContent = imageData.index;
        this.currentFilenameElem.textContent = imageData.filename;
        this.currentRowElem.textContent = imageData.row;
        this.currentColElem.textContent = imageData.col;
        
        // Load image
        const imageURL = api.getImageURL(imageData.path || imageData.filename);
        console.log('Image URL:', imageURL);
        
        this.currentImage.src = imageURL;
        this.currentImage.style.display = 'block';
        this.canvasOverlay.classList.remove('hidden');
        
        // Update progress
        await api.updateProgress(index, false);
        this.updateProgress();
        
        // Update navigation buttons
        this.updateNavigationButtons();
    }

    /**
     * Handle image loaded event
     */
    async onImageLoaded() {
        // Hide overlay
        this.canvasOverlay.classList.add('hidden');
        
        // Initialize canvas manager if needed
        if (!this.canvasManager) {
            this.canvasManager = new CanvasManager('annotation-canvas', 'current-image');
            this.canvasManager.onBoxAdded = () => this.updateBoxesList();
            this.canvasManager.onBoxDeleted = () => this.updateBoxesList();
        }
        
        // Resize canvas to match DISPLAYED image size (not natural size)
        // This accounts for the 50% CSS scaling
        const width = this.currentImage.clientWidth;
        const height = this.currentImage.clientHeight;
        
        console.log('Natural image size:', this.currentImage.naturalWidth, 'x', this.currentImage.naturalHeight);
        console.log('Displayed image size:', width, 'x', height);
        
        this.canvasManager.resizeCanvas(width, height);
        
        // Load existing annotation
        await this.loadExistingAnnotation();
        
        this.setStatus('Image loaded. Draw boxes around plastic or mark as "No Plastic"', 'info');
    }

    /**
     * Load existing annotation for current image
     */
    async loadExistingAnnotation() {
        try {
            const sheetRow = this.images[this.currentIndex]?.row;
            const response = await api.getAnnotation(this.currentIndex, Number.isInteger(sheetRow) ? sheetRow : null);
            
            if (response.annotation) {
                const annotation = response.annotation;
                this.setPlasticLabel(!!annotation.has_plastic);
                
                if (annotation.boxes && annotation.boxes.length > 0) {
                    this.canvasManager.setBoxesFromNormalized(annotation.boxes);
                } else {
                    this.canvasManager.clearBoxes();
                }
                
                this.updateBoxesList();
            } else {
                this.setPlasticLabel(null);
                this.canvasManager.clearBoxes();
                this.updateBoxesList();
            }
        } catch (error) {
            console.error('Error loading annotation:', error);
        }
    }

    /**
     * Save current annotation
     */
    async saveCurrentAnnotation() {
        if (!this.canvasManager) return;
        
        const boxes = this.canvasManager.getBoxesNormalized();
        let hasPlastic = this.currentLabel;

        // If location boxes exist, plastic is present regardless of current label state.
        if (boxes.length > 0) {
            hasPlastic = true;
            if (this.currentLabel !== true) {
                this.setPlasticLabel(true);
            }
        }

        if (hasPlastic === null) {
            hasPlastic = false;
        }
        
        const annotation = {
            has_plastic: hasPlastic,
            boxes: boxes,
            image_filename: this.images[this.currentIndex].filename,
            sheet_row: this.images[this.currentIndex].row,
            annotated_at: new Date().toISOString()
        };
        
        try {
            const result = await api.saveAnnotation(this.currentIndex, annotation);
            this.pendingSheetWrites = result.queue_size || 0;

            if ((result.flushed || 0) > 0) {
                this.setStatus(`Saved locally. Synced ${result.flushed} rows to sheet (${this.pendingSheetWrites} pending).`, 'success');
            } else {
                this.setStatus(`Saved locally. ${this.pendingSheetWrites} pending sheet writes.`, 'success');
            }
        } catch (error) {
            this.setStatus('Failed to save annotation', 'error');
            console.error('Save error:', error);
        }
    }

    /**
     * Start periodic queue flush for better throughput.
     */
    startFlushTimer() {
        this.stopFlushTimer();
        this.flushIntervalId = setInterval(async () => {
            if (!this.isAuthenticated || !this.sheetConnected) return;
            try {
                const status = await api.getSheetQueueStatus();
                this.pendingSheetWrites = status.queue_size || 0;
                if (this.pendingSheetWrites > 0) {
                    const result = await api.flushSheetQueue(100);
                    this.pendingSheetWrites = result.queue_size || 0;
                }
            } catch (error) {
                // Keep UI responsive even if background flush fails.
                console.warn('Background sheet flush failed:', error.message);
            }
        }, 8000);
    }

    /**
     * Stop periodic queue flush.
     */
    stopFlushTimer() {
        if (this.flushIntervalId) {
            clearInterval(this.flushIntervalId);
            this.flushIntervalId = null;
        }
    }

    /**
     * Mark current image as having plastic
     */
    markAsHasPlastic() {
        this.setPlasticLabel(true);
        this.setStatus('Marked as "Plastic". Draw boxes to store location.', 'info');
    }

    /**
     * Mark current image as having no plastic
     */
    async markAsNoPlastic() {
        this.setPlasticLabel(false);
        this.canvasManager.clearBoxes();
        await this.saveCurrentAnnotation();
        this.updateBoxesList();
        this.setStatus('Marked as "No Plastic"', 'success');
        
        // Auto-advance to next image
        setTimeout(() => this.nextImage(), 500);
    }

    /**
     * Clear all bounding boxes
     */
    clearAllBoxes() {
        if (confirm('Are you sure you want to clear all boxes?')) {
            this.canvasManager.clearBoxes();
            this.updateBoxesList();
            this.setStatus('All boxes cleared', 'info');
        }
    }

    /**
     * Update boxes list display
     */
    updateBoxesList() {
        const boxes = this.canvasManager.getBoxes();
        this.boxCount.textContent = boxes.length;
        
        if (boxes.length === 0) {
            this.boxesContainer.innerHTML = '<p class="empty-state">No boxes drawn yet</p>';
            this.clearAllBoxesBtn.disabled = true;
        } else {
            this.boxesContainer.innerHTML = boxes.map((box, index) => `
                <div class="box-item">
                    Box ${index + 1}: (${Math.round(box.x)}, ${Math.round(box.y)}) 
                    ${Math.round(box.width)}×${Math.round(box.height)}
                </div>
            `).join('');
            this.clearAllBoxesBtn.disabled = false;
        }
    }

    /**
     * Navigate to previous image
     */
    async previousImage() {
        if (this.currentIndex > 0) {
            await this.loadImage(this.currentIndex - 1);
        }
    }

    /**
     * Navigate to next image
     */
    async nextImage() {
        if (this.currentIndex < this.images.length - 1) {
            await this.loadImage(this.currentIndex + 1);
        }
    }

    /**
     * Jump to specific index
     */
    async jumpToIndex() {
        const index = parseInt(this.jumpIndex.value);
        
        if (isNaN(index) || index < 0 || index >= this.images.length) {
            this.setStatus('Invalid index', 'error');
            return;
        }
        
        await this.loadImage(index);
        this.jumpIndex.value = '';
    }

    /**
     * Update navigation buttons state
     */
    updateNavigationButtons() {
        this.prevBtn.disabled = this.currentIndex === 0;
        this.nextBtn.disabled = this.currentIndex >= this.images.length - 1;
    }

    /**
     * Enable controls after initialization
     */
    enableControls() {
        this.hasPlasticBtn.disabled = false;
        this.noPlasticBtn.disabled = false;
        this.updatePlasticLabelButtons();
        this.updateNavigationButtons();
    }

    /**
     * Set and render current plastic label state.
     */
    setPlasticLabel(value) {
        this.currentLabel = value;
        this.updatePlasticLabelButtons();
    }

    /**
     * Update label button visual state.
     */
    updatePlasticLabelButtons() {
        if (!this.hasPlasticBtn || !this.noPlasticBtn) return;

        this.hasPlasticBtn.classList.toggle('label-active', this.currentLabel === true);
        this.noPlasticBtn.classList.toggle('label-active', this.currentLabel === false);
    }

    /**
     * Update progress display
     */
    updateProgress() {
        if (this.images.length > 0) {
            this.progressText.textContent = 
                `Image ${this.currentIndex + 1} of ${this.images.length}`;
        }
    }

    /**
     * Set status message
     */
    setStatus(message, type = 'info') {
        this.statusMessage.textContent = message;
        this.statusMessage.className = type;
    }

    /**
     * Handle keyboard shortcuts
     */
    handleKeyboard(e) {
        if (!this.isInitialized) return;
        
        // Prevent shortcuts when typing in input fields
        if (e.target.tagName === 'INPUT') return;
        
        switch(e.key) {
            case 'ArrowLeft':
                e.preventDefault();
                this.previousImage();
                break;
            case 'ArrowRight':
                e.preventDefault();
                this.nextImage();
                break;
            case 'n':
            case 'N':
                e.preventDefault();
                this.markAsNoPlastic();
                break;
            case 'c':
            case 'C':
                e.preventDefault();
                this.clearAllBoxes();
                break;
        }
    }

    /**
     * Refresh Google auth status from backend.
     */
    async refreshAuthState() {
        const status = await api.getAuthStatus();
        this.isAuthenticated = !!status.authenticated;
        this.sheetConnected = !!status.sheet_connected;
        this.authStatusElem.textContent = this.isAuthenticated ? 'Connected to Google' : 'Not connected';
        this.googleLogoutBtn.disabled = !this.isAuthenticated;
        return this.isAuthenticated;
    }

    /**
     * Load current sheet config into the input field.
     */
    async loadSheetConfig() {
        try {
            const response = await api.getSheetConfig();
            this.sheetConnected = !!response.configured;
            this.sheetUrlInput.value = response.sheet_input || '';
        } catch (error) {
            // sheet not configured yet
            this.sheetConnected = false;
        }
    }

    /**
     * Connect sheet URL, load image list, and sync start index from backend progress.
     */
    async connectSheet() {
        if (!this.isAuthenticated) {
            this.setStatus('Sign in with Google first.', 'error');
            return;
        }

        const sheetInput = this.sheetUrlInput.value.trim();
        if (!sheetInput) {
            this.setStatus('Please paste a Google Sheet URL or Spreadsheet ID.', 'error');
            return;
        }

        try {
            await api.setSheetConfig(sheetInput);
            const imageResponse = await api.getImageList();
            this.images = imageResponse.images || [];
            this.sheetConnected = true;

            const progressResponse = await api.getProgress();
            const savedIndex = parseInt(progressResponse.progress.current_index, 10);
            this.currentIndex = Number.isNaN(savedIndex) ? 0 : savedIndex;
            this.startIndex.value = String(this.currentIndex);

            this.updateProgress();
            this.setStatus(`Sheet connected. Loaded ${this.images.length} images.`, 'success');
            this.startFlushTimer();
        } catch (error) {
            this.sheetConnected = false;
            this.setStatus(`Failed to connect sheet: ${error.message}`, 'error');
        }
    }

    /**
     * Start Google login in a popup and wait for success.
     */
    async loginWithGoogle() {
        try {
            const authURL = await api.startGoogleLogin();
            const popup = window.open(authURL, 'google-oauth', 'width=540,height=700');
            if (!popup) {
                this.setStatus('Popup blocked. Allow popups and try again.', 'error');
                return;
            }

            this.setStatus('Complete Google login in the popup window...', 'info');

            const started = Date.now();
            const timeoutMs = 120000;
            const poll = setInterval(async () => {
                try {
                    await this.refreshAuthState();
                    if (this.isAuthenticated) {
                        clearInterval(poll);
                        this.setStatus('Google login successful! Add and connect a sheet URL.', 'success');
                    }
                } catch (error) {
                    // ignore transient polling errors
                }

                if (Date.now() - started > timeoutMs) {
                    clearInterval(poll);
                    this.setStatus('Google login timed out. Please try again.', 'error');
                }
            }, 1200);
        } catch (error) {
            this.setStatus('Failed to start Google login: ' + error.message, 'error');
        }
    }

    /**
     * Log out current Google session.
     */
    async logoutGoogle() {
        try {
            await api.logout();
            this.images = [];
            this.isAuthenticated = false;
            this.sheetConnected = false;
            this.sheetUrlInput.value = '';
            this.pendingSheetWrites = 0;
            this.stopFlushTimer();
            this.authStatusElem.textContent = 'Not connected';
            this.googleLogoutBtn.disabled = true;
            this.updateProgress();
            this.setStatus('Signed out from Google session.', 'info');
        } catch (error) {
            this.setStatus('Failed to sign out.', 'error');
        }
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    const app = new AnnotationApp();
});
