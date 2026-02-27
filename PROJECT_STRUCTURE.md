# Project Structure

```
nest-train/
├── backend/                          # Flask Backend Server
│   ├── app.py                       # Main Flask application with REST API
│   ├── config.py                    # Configuration settings
│   ├── requirements.txt             # Python dependencies
│   └── utils/
│       ├── __init__.py
│       ├── data_handler.py          # CSV/Excel reading and image list management
│       └── annotation_handler.py    # Annotation storage and export
│
├── frontend/                         # Web Interface
│   ├── index.html                   # Main HTML page
│   ├── css/
│   │   └── styles.css              # Complete styling for the interface
│   └── js/
│       ├── api.js                  # Backend API communication
│       ├── canvas.js               # Bounding box drawing logic
│       └── app.js                  # Main application controller
│
├── data/                            # Data Storage
│   ├── images/                      # Place your bird nest images here
│   │   └── README.md               # Instructions for images directory
│   ├── annotations/                 # Auto-generated annotation files (JSON)
│   │   └── README.md               # Annotation format documentation
│   ├── image_list.csv              # List of images to annotate
│   └── progress.json               # Auto-generated progress tracking
│
├── start.sh                         # Quick start script (Unix/Mac)
├── prepare_data.py                  # Helper script to generate image_list.csv
├── README.md                        # Full documentation
├── QUICKSTART.md                    # Quick start guide
└── .gitignore                       # Git ignore rules
```

## File Descriptions

### Backend Files

- **app.py**: Flask server with REST API endpoints for image serving, annotation CRUD, and progress tracking
- **config.py**: Centralized configuration for paths, server settings, and supported formats
- **utils/data_handler.py**: Handles reading image lists from CSV/Excel files
- **utils/annotation_handler.py**: Manages saving/loading annotations with automatic backup
- **requirements.txt**: Python package dependencies (Flask, pandas, Pillow, etc.)

### Frontend Files

- **index.html**: Single-page application with image viewer and annotation controls
- **css/styles.css**: Modern, responsive styling with clean UI/UX
- **js/api.js**: API client for backend communication
- **js/canvas.js**: Interactive canvas for drawing/editing bounding boxes
- **js/app.js**: Main application logic, state management, and event handling

### Data Files

- **data/images/**: Store your bird nest images here
- **data/annotations/**: Automatically populated with annotation JSON files
- **data/image_list.csv**: Links images to metadata (row/col from original spreadsheet)
- **data/progress.json**: Tracks current annotation position (auto-generated)

### Helper Scripts

- **start.sh**: One-command startup script (sets up venv, installs deps, starts server)
- **prepare_data.py**: Scans images folder and generates image_list.csv automatically

## Key Features Implemented

✅ **Auto-save**: Annotations saved automatically when navigating images
✅ **Progress tracking**: Resume from where you stopped
✅ **Bounding box drawing**: Interactive click-and-drag interface
✅ **Multi-box support**: Draw multiple boxes per image
✅ **Box deletion**: Right-click to delete individual boxes
✅ **No plastic marking**: Quick button for images without plastic
✅ **Keyboard shortcuts**: Efficient navigation (arrows, N, C keys)
✅ **Export functionality**: Download all annotations as JSON
✅ **Backup system**: Automatic backup before overwriting annotations
✅ **Normalized coordinates**: Boxes stored in 0-1 scale for ML compatibility
✅ **Spreadsheet integration**: Load from CSV or Excel files
✅ **Responsive UI**: Works on different screen sizes
✅ **Error handling**: Robust error handling throughout

## Data Flow

1. **Startup**: Frontend loads image list from backend
2. **Display**: Images served from backend to frontend canvas
3. **Annotation**: User draws boxes → stored in canvas state
4. **Save**: On navigation → boxes sent to backend → saved as JSON
5. **Progress**: Current index auto-updated in progress.json
6. **Resume**: Next session starts from last saved position
7. **Export**: All annotations compiled into single JSON file

## Technologies Used

- **Backend**: Python, Flask, pandas, Pillow
- **Frontend**: Vanilla JavaScript, HTML5 Canvas, CSS3
- **Data Format**: JSON (COCO-style compatible)
- **Storage**: File-based (JSON files, easily portable)
