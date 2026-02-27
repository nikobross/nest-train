/**
 * Canvas Manager for drawing bounding boxes
 */

class CanvasManager {
    constructor(canvasId, imageId) {
        this.canvas = document.getElementById(canvasId);
        this.ctx = this.canvas.getContext('2d');
        this.image = document.getElementById(imageId);
        
        this.boxes = [];
        this.currentBox = null;
        this.isDrawing = false;
        this.startX = 0;
        this.startY = 0;
        
        this.setupEventListeners();
    }

    /**
     * Setup canvas event listeners
     */
    setupEventListeners() {
        this.canvas.addEventListener('mousedown', this.handleMouseDown.bind(this));
        this.canvas.addEventListener('mousemove', this.handleMouseMove.bind(this));
        this.canvas.addEventListener('mouseup', this.handleMouseUp.bind(this));
        this.canvas.addEventListener('contextmenu', this.handleRightClick.bind(this));
    }

    /**
     * Resize canvas to match image dimensions
     */
    resizeCanvas(width, height) {
        this.canvas.width = width;
        this.canvas.height = height;
        this.redraw();
    }

    /**
     * Handle mouse down - start drawing
     */
    handleMouseDown(e) {
        if (e.button !== 0) return; // Only left click
        
        const rect = this.canvas.getBoundingClientRect();
        this.startX = e.clientX - rect.left;
        this.startY = e.clientY - rect.top;
        this.isDrawing = true;
        
        this.currentBox = {
            x: this.startX,
            y: this.startY,
            width: 0,
            height: 0
        };
    }

    /**
     * Handle mouse move - update current box
     */
    handleMouseMove(e) {
        if (!this.isDrawing) return;
        
        const rect = this.canvas.getBoundingClientRect();
        const currentX = e.clientX - rect.left;
        const currentY = e.clientY - rect.top;
        
        this.currentBox.width = currentX - this.startX;
        this.currentBox.height = currentY - this.startY;
        
        this.redraw();
    }

    /**
     * Handle mouse up - finish drawing
     */
    handleMouseUp(e) {
        if (!this.isDrawing) return;
        
        this.isDrawing = false;
        
        // Only add box if it has meaningful size
        if (Math.abs(this.currentBox.width) > 5 && Math.abs(this.currentBox.height) > 5) {
            // Normalize the box (handle negative width/height)
            const normalizedBox = this.normalizeBox(this.currentBox);
            this.boxes.push(normalizedBox);
            this.onBoxAdded && this.onBoxAdded(normalizedBox);
        }
        
        this.currentBox = null;
        this.redraw();
    }

    /**
     * Handle right click - delete box
     */
    handleRightClick(e) {
        e.preventDefault();
        
        const rect = this.canvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        
        // Find if click is inside any box
        for (let i = this.boxes.length - 1; i >= 0; i--) {
            const box = this.boxes[i];
            if (x >= box.x && x <= box.x + box.width &&
                y >= box.y && y <= box.y + box.height) {
                this.boxes.splice(i, 1);
                this.onBoxDeleted && this.onBoxDeleted(i);
                this.redraw();
                break;
            }
        }
    }

    /**
     * Normalize box coordinates (handle negative dimensions)
     */
    normalizeBox(box) {
        let { x, y, width, height } = box;
        
        if (width < 0) {
            x += width;
            width = Math.abs(width);
        }
        
        if (height < 0) {
            y += height;
            height = Math.abs(height);
        }
        
        return { x, y, width, height };
    }

    /**
     * Redraw all boxes on canvas
     */
    redraw() {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Draw existing boxes
        this.boxes.forEach((box, index) => {
            this.drawBox(box, '#2563eb', 3);
            this.drawBoxLabel(box, `Box ${index + 1}`);
        });
        
        // Draw current box being drawn
        if (this.currentBox && this.isDrawing) {
            this.drawBox(this.currentBox, '#f59e0b', 2, true);
        }
    }

    /**
     * Draw a single box
     */
    drawBox(box, color, lineWidth, dashed = false) {
        this.ctx.strokeStyle = color;
        this.ctx.lineWidth = lineWidth;
        
        if (dashed) {
            this.ctx.setLineDash([5, 5]);
        } else {
            this.ctx.setLineDash([]);
        }
        
        this.ctx.strokeRect(box.x, box.y, box.width, box.height);
        
        // Draw semi-transparent fill
        this.ctx.fillStyle = color + '20';
        this.ctx.fillRect(box.x, box.y, box.width, box.height);
    }

    /**
     * Draw label for a box
     */
    drawBoxLabel(box, label) {
        this.ctx.font = '14px sans-serif';
        this.ctx.fillStyle = '#2563eb';
        this.ctx.fillText(label, box.x + 5, box.y + 20);
    }

    /**
     * Clear all boxes
     */
    clearBoxes() {
        this.boxes = [];
        this.redraw();
    }

    /**
     * Load boxes from data
     */
    loadBoxes(boxes) {
        this.boxes = boxes || [];
        this.redraw();
    }

    /**
     * Get all boxes
     */
    getBoxes() {
        return this.boxes;
    }

    /**
     * Get boxes in normalized format (0-1 scale)
     */
    getBoxesNormalized() {
        const width = this.canvas.width;
        const height = this.canvas.height;
        
        return this.boxes.map(box => ({
            x: box.x / width,
            y: box.y / height,
            width: box.width / width,
            height: box.height / height
        }));
    }

    /**
     * Set boxes from normalized format (0-1 scale)
     */
    setBoxesFromNormalized(normalizedBoxes) {
        const width = this.canvas.width;
        const height = this.canvas.height;
        
        this.boxes = normalizedBoxes.map(box => ({
            x: box.x * width,
            y: box.y * height,
            width: box.width * width,
            height: box.height * height
        }));
        
        this.redraw();
    }
}
