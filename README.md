# 🪹 Bird Nest Plastic Annotation Tool

A robust web-based tool for creating training data for AI classifiers that detect plastic in bird nests. This tool allows annotators to draw bounding boxes around plastic objects in images and automatically saves progress.

## 🚀 Quick Start (Google Sheets Users)

If your images are in a Google Spreadsheet with URLs:

```bash
# 1. Export your Google Sheet as .tsv (File → Download → Tab-separated values)

# 2. Run the automated workflow
./workflow_example.sh your_sheet.tsv 50

# 3. Open frontend/index.html in your browser

# 4. Start annotating! 🎨
```

**That's it!** See [EXTRACTION_GUIDE.md](EXTRACTION_GUIDE.md) for more options.

## 📚 Documentation

- **[COMMANDS.md](COMMANDS.md)** - Quick command reference (⭐ Start here!)
- **[QUICKSTART.md](QUICKSTART.md)** - Step-by-step setup guide
- **[EXTRACTION_GUIDE.md](EXTRACTION_GUIDE.md)** - Extract images from Google Sheets
- **[PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)** - Detailed project overview

## Features

- ✨ **Interactive Bounding Box Drawing**: Click and drag to draw boxes around plastic objects
- 💾 **Auto-Save**: Automatically saves annotations when moving between images
- 📍 **Progress Tracking**: Resume annotation from where you left off
- ⌨️ **Keyboard Shortcuts**: Efficient navigation and annotation controls
- 📊 **Spreadsheet Integration**: Load image lists from CSV or Excel files
- 🌐 **Google Sheets Support**: Extract images directly from Google Spreadsheet exports
- 📦 **Export Functionality**: Export annotations in ML-ready JSON format
- 🔄 **Backup System**: Automatic backup of annotations to prevent data loss
- 🎯 **Smart Filtering**: Filter images by plastic presence (yes/no/unsure)
- 🖼️ **Optimized Display**: Images shown at 50% size for easier viewing (coordinates auto-adjusted)

## Project Structure

```
nest-train/
├── backend/                 # Flask backend server
│   ├── app.py              # Main Flask application
│   ├── config.py           # Configuration settings
│   ├── requirements.txt    # Python dependencies
│   └── utils/
│       ├── data_handler.py        # Spreadsheet reading
│       └── annotation_handler.py  # Annotation storage
├── frontend/               # Web interface
│   ├── index.html         # Main HTML page
│   ├── css/
│   │   └── styles.css     # Styling
│   └── js/
│       ├── app.js         # Main application logic
│       ├── canvas.js      # Bounding box drawing
│       └── api.js         # Backend communication
├── data/
│   ├── images/            # Your bird nest images
│   ├── annotations/       # Saved annotations (JSON)
│   ├── image_list.csv     # List of images to annotate
│   └── progress.json      # Current annotation progress
└── README.md
```

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- A modern web browser (Chrome, Firefox, Safari, or Edge)

### Installation

1. **Clone or navigate to the repository**:
   ```bash
   cd /Users/nikoross/Github/nest-train
   ```

2. **Create a Python virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Python dependencies**:
   ```bash
   pip install -r backend/requirements.txt
   ```

4. **Prepare your data**:
   
   **Option A - Extract from Google Spreadsheet** (Recommended):
   ```bash
   # Export your Google Sheet as .tsv file, then:
   python3 extract_images.py your_sheet.tsv -n 50
   # See EXTRACTION_GUIDE.md for details
   ```
   
   **Option B - Manual Setup**:
   - Place your bird nest images in `data/images/`
   - Update `data/image_list.csv` with your image filenames
   - Or use `python3 prepare_data.py` to auto-generate from images

### CSV/Excel Format

Your spreadsheet should have the following columns:

| image_path | row | col |
|------------|-----|-----|
| bird_nest_001.jpg | 1 | A |
| bird_nest_002.jpg | 2 | A |
| bird_nest_003.jpg | 3 | A |

- **image_path**: Filename of the image (required)
- **row**: Row number in your original spreadsheet (optional)
- **col**: Column letter in your original spreadsheet (optional)

> **Note**: The `row` and `col` columns are optional and used for tracking the source location in your original spreadsheet.

## Extracting Images from Google Spreadsheet

If your images are referenced in a Google Spreadsheet with URLs (like the NestWatch database), use the extraction script:

### Quick Extract

```bash
# 1. Export your Google Sheet as .tsv
#    (File → Download → Tab-separated values)

# 2. Extract images
python3 extract_images.py your_sheet.tsv -n 50
```

### Extract Options

```bash
# Get only images with plastic
python3 extract_images.py your_sheet.tsv -f y

# Get only images without plastic (negative samples)
python3 extract_images.py your_sheet.tsv -f n -n 100

# Get unsure images for review
python3 extract_images.py your_sheet.tsv -f u
```

The script will:
- Download images from URLs in your spreadsheet
- Save them to `data/images/` with proper naming
- Create `data/image_list.csv` automatically
- Preserve original metadata and plastic status

**See [EXTRACTION_GUIDE.md](EXTRACTION_GUIDE.md) for detailed instructions.**

## Running the Application

### 1. Start the Backend Server

```bash
# Make sure you're in the virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Run the Flask server
cd backend
python app.py
```

The server will start on `http://localhost:5001`

### 2. Open the Frontend

Open `frontend/index.html` in your web browser:

```bash
# From the project root
open frontend/index.html  # macOS
# or
xdg-open frontend/index.html  # Linux
# or simply double-click the file in Windows Explorer
```

Alternatively, you can serve the frontend with a simple HTTP server:

```bash
# From the project root
python3 -m http.server 8000 --directory frontend
```

Then open `http://localhost:8000` in your browser.

## Usage Guide

### Starting Annotation

1. **Set Start Position** (optional):
   - Enter the index number in "Start at Index" field
   - Click "Start Annotation"
   - Or leave at 0 to start from the beginning

2. **Annotating Images**:

   **If there IS plastic:**
   - Click and drag on the image to draw bounding boxes around plastic objects
   - You can draw multiple boxes per image
   - Right-click on a box to delete it
   - Click "Next →" when done

   **If there is NO plastic:**
   - Click the "✗ No Plastic" button
   - The tool will auto-advance to the next image

3. **Navigation**:
   - Use "← Previous" and "Next →" buttons
   - Or use keyboard arrow keys (← →)
   - Jump to specific image using "Jump to Index"

### Keyboard Shortcuts

- `←` - Previous image
- `→` - Next image  
- `N` - Mark as "No Plastic"
- `C` - Clear all boxes

### Saving and Progress

- **Auto-Save**: Annotations are automatically saved when you navigate to another image
- **Progress Tracking**: Your current position is saved automatically
- **Resume**: Next time you start, you can resume from where you left off

### Exporting Annotations

Click the "Export Annotations" button in the top-right to download all annotations as `annotations_export.json`. The file is saved to:
- **Server**: `data/annotations_export.json`
- **Download**: `annotations_export.json` (downloaded to your browser's default folder)

Each export overwrites the previous one (a backup is kept as `annotations_export.backup.json`). The export format is compatible with common ML frameworks.

## Annotation Data Format

Annotations are saved as JSON files in `data/annotations/`:

```json
{
  "image_index": 0,
  "has_plastic": true,
  "boxes": [
    {
      "x": 0.2534,
      "y": 0.3421,
      "width": 0.1234,
      "height": 0.0987
    }
  ],
  "image_filename": "bird_nest_001.jpg",
  "annotated_at": "2026-02-27T10:30:00",
  "timestamp": "2026-02-27T10:30:00"
}
```

**Note**: Bounding box coordinates are normalized (0-1 scale) relative to image dimensions for ML compatibility.

## API Endpoints

The backend provides the following REST API endpoints:

- `GET /api/health` - Health check
- `GET /api/images/list` - Get list of all images
- `GET /api/images/<filename>` - Serve image file
- `GET /api/progress` - Get current progress
- `POST /api/progress` - Update progress
- `GET /api/annotations/<index>` - Get annotation for image
- `POST /api/annotations/<index>` - Save annotation
- `GET /api/annotations/export` - Export all annotations

## Configuration

### Backend Settings

Edit `backend/config.py` to customize:

- Server host and port
- Data directories
- Supported image formats
- Auto-save settings
- Backup settings

### Image Display Size

Images are displayed at 50% of original size for easier viewing. Coordinates are automatically normalized, so annotations remain accurate.

To change display size, edit `frontend/css/styles.css`:

```css
#current-image {
    max-width: 50%;  /* Change to 75%, 100%, 33%, etc. */
}
```

See [IMAGE_DISPLAY.md](IMAGE_DISPLAY.md) for technical details.

## Troubleshooting

### Backend won't start
- Ensure Python virtual environment is activated
- Check all dependencies are installed: `pip install -r backend/requirements.txt`
- Verify Python version is 3.8+

### Images not loading
- Check that images are in `data/images/` directory
- Verify image paths in `image_list.csv` match actual filenames
- Ensure backend server is running

### CORS errors in browser
- Make sure you're accessing the frontend from the same origin as the backend
- Or use a simple HTTP server to serve the frontend

### Annotations not saving
- Check backend console for error messages
- Verify write permissions on `data/annotations/` directory
- Check browser console for API errors

## Contributing

This tool was designed to be simple and extensible. Feel free to:

- Add support for additional annotation types (polygons, keypoints, etc.)
- Implement user authentication for multi-user scenarios
- Add annotation quality checks
- Integrate with cloud storage
- Add more export formats (COCO, YOLO, Pascal VOC, etc.)

## License

This project is open source. Use it for your research and conservation efforts!

## Support

For questions or issues, please check the troubleshooting section or create an issue in the repository.

---

**Happy Annotating! 🦅🪹**
