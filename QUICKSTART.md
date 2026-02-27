# Quick Start Guide

## For First-Time Users

### Step 1: Install Dependencies

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install requirements
pip install -r backend/requirements.txt
```

### Step 2: Add Your Images

**Option A: Extract from Google Spreadsheet** (Recommended)

```bash
# Export your Google Sheet as .tsv file first
# Then run:
python3 extract_images.py your_sheet.tsv -n 50

# See EXTRACTION_GUIDE.md for detailed instructions
```

**Option B: Manual Setup**

1. Copy your bird nest images to `data/images/`
2. Create a CSV file listing your images

**Example CSV** (`data/image_list.csv`):
```csv
image_path,row,col
nest_001.jpg,1,A
nest_002.jpg,2,A
nest_003.jpg,3,A
```

### Step 3: Start the Server

```bash
cd backend
python app.py
```

You should see:
```
 * Running on http://0.0.0.0:5001
```

### Step 4: Open the Interface

Open `frontend/index.html` in your web browser.

### Step 5: Start Annotating

1. Enter starting index (or leave at 0)
2. Click "Start Annotation"
3. Draw boxes around plastic or click "No Plastic"
4. Use arrow keys to navigate between images

## Tips

- **Auto-save is enabled**: No need to manually save
- **Resume anytime**: Your progress is automatically saved
- **Keyboard shortcuts**: Use arrow keys for quick navigation
- **Export when done**: Click "Export Annotations" to get your data

## Common Commands

```bash
# Activate environment
source venv/bin/activate

# Start backend
cd backend && python app.py

# Deactivate environment when done
deactivate
```

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Customize settings in `backend/config.py`
- Export annotations and start training your model!
