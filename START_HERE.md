# 🪹 Bird Nest Plastic Annotation Tool

Complete image annotation tool for creating AI training data to detect plastic in bird nests.

---

## ⚡ Super Quick Start

```bash
# Have images in Google Sheets? Start here:
./workflow_example.sh your_sheet.tsv 50

# Have local images? Start here:
python3 prepare_data.py
./start.sh
```

Then open `frontend/index.html` in your browser. Done! 🎉

---

## 📖 Documentation Index

| Document | Purpose | When to Use |
|----------|---------|-------------|
| **[COMMANDS.md](COMMANDS.md)** | Quick command reference | Need a quick command |
| **[QUICKSTART.md](QUICKSTART.md)** | Step-by-step setup | First time setup |
| **[EXTRACTION_GUIDE.md](EXTRACTION_GUIDE.md)** | Google Sheets extraction | Images in spreadsheet |
| **[README.md](README.md)** | Full documentation | Detailed information |
| **[PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)** | Code organization | Understanding codebase |

---

## 🎯 What This Tool Does

1. **Display** bird nest images from your collection
2. **Draw** bounding boxes around plastic objects
3. **Mark** images with no plastic
4. **Auto-save** your annotations as you work
5. **Resume** from where you stopped
6. **Export** all annotations for ML training

---

## 🚀 Three Ways to Start

### Method 1: Google Sheets (Automated)

Your images are URLs in a Google Spreadsheet:

```bash
# Export sheet as .tsv, then:
./workflow_example.sh your_sheet.tsv 50
```

### Method 2: Google Sheets (Manual)

```bash
# Install dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt

# Extract images (50 with plastic only)
python3 extract_images.py your_sheet.tsv -f y -n 50

# Start server
./start.sh
```

### Method 3: Local Images

```bash
# Copy images to data/images/
# Auto-generate CSV:
python3 prepare_data.py

# Start server:
./start.sh
```

---

## 📋 Example Files

Try the tool with example data:
- `example_sheet.tsv` - Sample spreadsheet format
- See `EXTRACTION_GUIDE.md` for testing

---

## 🛠️ Features

- ✅ Interactive bounding box drawing
- ✅ Auto-save on navigation
- ✅ Progress tracking & resume
- ✅ Keyboard shortcuts (←→NC)
- ✅ Google Sheets integration
- ✅ Filter by plastic status (y/n/u)
- ✅ Export to ML-ready JSON
- ✅ Automatic backups

---

## 📁 Project Structure

```
nest-train/
├── backend/           # Flask API server
├── frontend/          # Web interface
├── data/
│   ├── images/       # Your images
│   ├── annotations/  # Auto-saved annotations
│   └── image_list.csv
├── extract_images.py  # Google Sheets→images
├── prepare_data.py    # Local images→CSV
├── start.sh          # Start server
└── workflow_example.sh # Complete workflow
```

---

## 💡 Common Tasks

### Download first 10 images to test
```bash
python3 extract_images.py data.tsv -n 10
./start.sh
```

### Get only images with plastic
```bash
python3 extract_images.py data.tsv -f y -n 100
```

### Get balanced dataset
```bash
python3 extract_images.py data.tsv -f y -n 50  # With plastic
python3 extract_images.py data.tsv -f n -n 50  # Without plastic
```

### Export annotations
Click "Export Annotations" button in the web interface

---

## ⌨️ Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `←` | Previous image |
| `→` | Next image |
| `N` | Mark "No Plastic" |
| `C` | Clear all boxes |

---

## 🔧 Troubleshooting

**Backend won't start?**
```bash
source venv/bin/activate
pip install -r backend/requirements.txt
```

**Images not loading?**
```bash
ls data/images/  # Check images exist
cat data/image_list.csv  # Check CSV is valid
```

**Browser CORS errors?**
```bash
python3 -m http.server 8000 --directory frontend
# Open http://localhost:8000
```

---

## 📊 Google Sheets Format

Your spreadsheet should have:
- `sub_id` column - Unique identifier
- `list` column - Image URLs
- `Anthropogenic materials present?...` - Plastic status (y/n/u)

See `example_sheet.tsv` for format.

---

## 🎓 Workflow Example

1. Export Google Sheet → `nest_data.tsv`
2. Extract 50 images → `python3 extract_images.py nest_data.tsv -n 50`
3. Start server → `./start.sh`
4. Open → `frontend/index.html`
5. Annotate images
6. Export → Click "Export Annotations"
7. Train your model! 🤖

---

## 📦 Output Format

Annotations saved as JSON with normalized coordinates (0-1):

```json
{
  "has_plastic": true,
  "boxes": [
    {"x": 0.25, "y": 0.34, "width": 0.12, "height": 0.09}
  ],
  "image_filename": "S56626974_5DB0A12E.jpeg",
  "annotated_at": "2026-02-27T10:30:00"
}
```

**Export file**: `data/annotations_export.json` (overwrites each time, previous saved as `.backup.json`)

---

## 🤝 Support

- Full details: [README.md](README.md)
- Quick commands: [COMMANDS.md](COMMANDS.md)
- Setup help: [QUICKSTART.md](QUICKSTART.md)
- Extraction: [EXTRACTION_GUIDE.md](EXTRACTION_GUIDE.md)

---

**Happy Annotating! 🦅🪹**

Built for bird conservation and AI research.
