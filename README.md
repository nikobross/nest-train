# Bird Nest Plastic Annotation Tool

Web-based annotation tool for drawing plastic bounding boxes on bird nest images. Data now flows directly from Google Sheets using OAuth.

## Quick Start

1. Create and activate a virtual environment.
2. Install dependencies.
3. Configure Google OAuth credentials.
4. Start backend and frontend.
5. Sign in with Google, connect your sheet URL, annotate.

```bash
cd /Users/nikoross/Github/nest-train
python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt
cp backend/.env.example backend/.env
```

Edit backend/.env with your Google OAuth values.

```bash
# terminal 1
cd backend
python app.py

# terminal 2
cd /Users/nikoross/Github/nest-train
python3 -m http.server 8000 --directory frontend
```

Open http://localhost:8000.

## Required Google Sheet Columns

At least one of these columns must exist for image paths/URLs:

- image_url
- image_path
- url
- list
- image

Annotation columns are auto-created on first save:

- has_plastic
- boxes_json
- annotated_at
- image_filename
- image_index

## OAuth Environment Variables

Set these in backend/.env:

- GOOGLE_CLIENT_ID
- GOOGLE_CLIENT_SECRET
- GOOGLE_REDIRECT_URI (default: http://localhost:5001/api/auth/google-callback)
- FLASK_SECRET_KEY
- DEFAULT_SHEET_URL (optional fallback if UI field is empty)

## Features

- Interactive bounding box drawing
- Auto-save on navigation
- Local progress tracking in data/progress.json
- Google OAuth login in-session
- Direct Google Sheets read/write for annotations
- Downloadable JSON export and sheet sync

## Documentation

- COMMANDS.md
- QUICKSTART.md
- PROJECT_STRUCTURE.md

## Notes

- Frontend should be served over HTTP (not opened as file) for reliable OAuth/session behavior.
- Local JSON annotations are still written as a backup in data/annotations.
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
