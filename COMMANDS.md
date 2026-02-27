# 🪹 Quick Command Reference

## Complete Workflow (From Google Sheets)

```bash
# 1. Export from Google Sheets (File → Download → .tsv)

# 2. Extract 50 images and start annotation
./workflow_example.sh nest_data.tsv 50

# 3. Open frontend/index.html in browser
```

## Image Extraction Commands

```bash
# Basic extraction (first 50 images)
python3 extract_images.py data.tsv -n 50

# Extract only images WITH plastic
python3 extract_images.py data.tsv -f y

# Extract only images WITHOUT plastic
python3 extract_images.py data.tsv -f n -n 100

# Extract unsure images
python3 extract_images.py data.tsv -f u

# Extract ALL images (no limit)
python3 extract_images.py data.tsv
```

## Server Commands

```bash
# Quick start (one command)
./start.sh

# Manual start
source venv/bin/activate
cd backend && python app.py

# Stop server
Ctrl+C
```

## Setup Commands

```bash
# First time setup
python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt

# Auto-generate CSV from local images
python3 prepare_data.py
```

## Common Workflows

### Workflow 1: Start with 10 test images
```bash
python3 extract_images.py data.tsv -n 10
./start.sh
# Open frontend/index.html
```

### Workflow 2: Annotate only plastic-positive images
```bash
python3 extract_images.py data.tsv -f y -n 100
./start.sh
# Open frontend/index.html
```

### Workflow 3: Get balanced dataset
```bash
# 100 with plastic
python3 extract_images.py data.tsv -f y -n 100

# 100 without plastic (append to same folder)
python3 extract_images.py data.tsv -f n -n 100

./start.sh
# Open frontend/index.html
```

### Workflow 4: Local images (no Google Sheets)
```bash
# Copy images to data/images/
python3 prepare_data.py
./start.sh
# Open frontend/index.html
```

## During Annotation

### Keyboard Shortcuts
- `←` Previous image
- `→` Next image
- `N` Mark as "No Plastic"
- `C` Clear all boxes

### Navigation
- **Next/Previous**: Use buttons or arrow keys
- **Jump**: Enter index number and click "Go"
- **Start Position**: Set where to begin annotating

### Drawing Boxes
- **Left-click + drag**: Draw bounding box
- **Right-click on box**: Delete box
- Auto-saves when navigating to next image

## Export Annotations

```bash
# From the web interface:
Click "Export Annotations" button

# File locations:
data/annotations_export.json          # Main export file
data/annotations_export.backup.json   # Previous export backup
```

## Troubleshooting

```bash
# Backend not starting?
source venv/bin/activate
pip install -r backend/requirements.txt

# Images not loading?
# Check data/images/ has images
# Check data/image_list.csv exists
ls -la data/images/
cat data/image_list.csv

# CORS errors?
# Serve frontend with simple server:
python3 -m http.server 8000 --directory frontend
# Then open http://localhost:8000
```

## File Locations

```
Your annotations: data/annotations/*.json
Progress file:    data/progress.json
Image list:       data/image_list.csv
Images:           data/images/
Main export:      data/annotations_export.json
Backup export:    data/annotations_export.backup.json
```

## Quick Links

- Full docs: [README.md](README.md)
- Extraction guide: [EXTRACTION_GUIDE.md](EXTRACTION_GUIDE.md)
- Quick start: [QUICKSTART.md](QUICKSTART.md)
- Structure: [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)
