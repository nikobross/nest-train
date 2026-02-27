/**
 * Main Application Logic
 */

class AnnotationApp {
    constructor() {
        this.images = [];
        this.currentIndex = 0;
        this.canvasManager = null;
        this.isInitialized = false;
        
        this.initializeElements();
        this.setupEventListeners();
        this.init();
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
        
        // Export
        this.exportBtn.addEventListener('click', () => this.exportAnnotations());
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => this.handleKeyboard(e));
        
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
            
            // Load image list
            const response = await api.getImageList();
            this.images = response.images;
            console.log('✓ Loaded', this.images.length, 'images');
            
            // Load progress
            const progressData = await api.getProgress();
            this.currentIndex = progressData.progress.current_index;
            console.log('✓ Current progress index:', this.currentIndex);
            
            this.updateProgress();
            this.setStatus(`Ready! Found ${this.images.length} images. Click "Start Annotation" to begin.`, 'success');
            
        } catch (error) {
            this.setStatus('Failed to connect to server. Please ensure the backend is running on port 5001.', 'error');
            console.error('Initialization error:', error);
        }
    }

    /**
     * Start annotation from specified index
     */
    async startAnnotation() {
        const startIdx = parseInt(this.startIndex.value) || 0;
        
        console.log('Starting annotation at index:', startIdx);
        console.log('Total images available:', this.images.length);
        
        if (this.images.length === 0) {
            this.setStatus('No images found! Please check your data/image_list.csv', 'error');
            return;
        }
        
        if (startIdx < 0 || startIdx >= this.images.length) {
            this.setStatus(`Invalid start index. Must be between 0 and ${this.images.length - 1}`, 'error');
            return;
        }
        
        try {
            this.currentIndex = startIdx;
            await this.loadImage(this.currentIndex);
            this.isInitialized = true;
            
            // Enable controls
            this.enableControls();
            
            console.log('Annotation started successfully');
        } catch (error) {
            this.setStatus('Error starting annotation: ' + error.message, 'error');
            console.error('Start annotation error:', error);
        }
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
        const imageData = this.images[index];
        
        console.log('Loading image:', imageData);
        
        // Update info display
        this.currentIndexElem.textContent = imageData.index;
        this.currentFilenameElem.textContent = imageData.filename;
        this.currentRowElem.textContent = imageData.row;
        this.currentColElem.textContent = imageData.col;
        
        // Load image
        const imageURL = api.getImageURL(imageData.filename);
        console.log('Image URL:', imageURL);
        
        this.currentImage.src = imageURL;
        this.currentImage.style.display = 'block';
        this.canvasOverlay.classList.remove('hidden');
        
        // Update progress
        await api.updateProgress(index);
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
            const response = await api.getAnnotation(this.currentIndex);
            
            if (response.annotation) {
                const annotation = response.annotation;
                
                if (annotation.has_plastic && annotation.boxes) {
                    this.canvasManager.setBoxesFromNormalized(annotation.boxes);
                } else {
                    this.canvasManager.clearBoxes();
                }
                
                this.updateBoxesList();
            } else {
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
        const hasPlastic = boxes.length > 0;
        
        const annotation = {
            has_plastic: hasPlastic,
            boxes: boxes,
            image_filename: this.images[this.currentIndex].filename,
            annotated_at: new Date().toISOString()
        };
        
        try {
            await api.saveAnnotation(this.currentIndex, annotation);
            this.setStatus('Annotation saved', 'success');
        } catch (error) {
            this.setStatus('Failed to save annotation', 'error');
            console.error('Save error:', error);
        }
    }

    /**
     * Mark current image as having plastic
     */
    markAsHasPlastic() {
        this.setStatus('Draw bounding boxes around plastic', 'info');
        // User will draw boxes manually
    }

    /**
     * Mark current image as having no plastic
     */
    async markAsNoPlastic() {
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
        this.updateNavigationButtons();
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
     * Export all annotations
     */
    async exportAnnotations() {
        try {
            this.setStatus('Exporting annotations...', 'info');
            const response = await api.exportAnnotations();
            
            // Download as JSON file with consistent filename
            const dataStr = JSON.stringify(response.annotations, null, 2);
            const dataBlob = new Blob([dataStr], { type: 'application/json' });
            const url = URL.createObjectURL(dataBlob);
            
            const link = document.createElement('a');
            link.href = url;
            link.download = 'annotations_export.json';  // Consistent filename
            link.click();
            
            URL.revokeObjectURL(url);
            this.setStatus(`Exported ${response.annotations.total} annotations to annotations_export.json`, 'success');
            console.log('✓ Exported', response.annotations.total, 'annotations');
        } catch (error) {
            this.setStatus('Failed to export annotations', 'error');
            console.error('Export error:', error);
        }
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    const app = new AnnotationApp();
});
