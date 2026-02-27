# Image Extraction from Google Spreadsheet

This guide explains how to extract images from your Google Spreadsheet into the annotation tool.

## Quick Start

### Step 1: Export your Google Spreadsheet

1. Open your Google Spreadsheet
2. Go to **File → Download → Tab-separated values (.tsv)**
3. Save the file (e.g., `nest_data.tsv`) to your project directory

### Step 2: Install additional requirements

```bash
pip install -r extract_requirements.txt
```

### Step 3: Run the extraction script

**Download all images:**
```bash
python3 extract_images.py nest_data.tsv
```

**Download first 50 images only:**
```bash
python3 extract_images.py nest_data.tsv -n 50
```

**Download only images WITH plastic (y=Yes):**
```bash
python3 extract_images.py nest_data.tsv -f y
```

**Download only images WITHOUT plastic (n=No):**
```bash
python3 extract_images.py nest_data.tsv -f n
```

**Download only unsure images (u=Unsure):**
```bash
python3 extract_images.py nest_data.tsv -f u
```

**Combine options (50 images with plastic):**
```bash
python3 extract_images.py nest_data.tsv -n 50 -f y
```

## What the script does

1. ✅ Reads your exported spreadsheet (TSV/CSV/Excel)
2. ✅ Filters rows with valid image URLs in the `list` column
3. ✅ Downloads images to `data/images/`
4. ✅ Creates `data/image_list.csv` with metadata
5. ✅ Preserves original submission IDs and plastic status
6. ✅ Skips already downloaded images (safe to re-run)

## Output Structure

After running the script:

```
data/
├── images/
│   ├── S56626974_5DB0A12E-59A9-4C27.jpeg
│   ├── S56660880_693E99A4-102D-4D0D.jpeg
│   └── S56768041_CD9CB1F4-9BC7-486C.jpeg
└── image_list.csv
```

The CSV will include:
- `image_path` - Filename in images directory
- `sub_id` - Original submission ID from spreadsheet
- `url` - Original image URL
- `has_plastic_initial` - Original annotation (y/n/u)
- `notes` - Explanation of plastic status

## Command Line Options

```bash
python3 extract_images.py <spreadsheet> [options]

Arguments:
  spreadsheet           Path to exported file (.tsv, .csv, or .xlsx)

Options:
  -n, --max-images N    Download maximum N images (default: all)
  -f, --filter-plastic  Filter by plastic: y/n/u (default: all)
  --skip-download       Only create CSV, don't download
  -h, --help           Show help message
```

## Examples

### Example 1: Get a sample for testing
```bash
python3 extract_images.py nest_data.tsv -n 10
```

### Example 2: Download all images with plastic for training
```bash
python3 extract_images.py nest_data.tsv -f y
```

### Example 3: Download images without plastic for negative samples
```bash
python3 extract_images.py nest_data.tsv -f n -n 100
```

### Example 4: Get unsure images for manual review
```bash
python3 extract_images.py nest_data.tsv -f u
```

## Spreadsheet Format

Your spreadsheet should have these columns (at minimum):
- `sub_id` - Submission identifier
- `list` - Image URL (must start with http)
- `Anthropogenic materials present?...` - Plastic status (y/n/u)

The script will work with your exact spreadsheet structure as shown.

## Troubleshooting

### "Spreadsheet not found"
- Make sure you've exported the file from Google Sheets
- Check the file path is correct
- Use tab-separated (.tsv) or comma-separated (.csv) format

### "Download failed"
- Check your internet connection
- Some images may have expired URLs
- The script will continue with other images

### "Column not found"
- Verify your export includes the `list` column with URLs
- Check if column names match (case-sensitive)

## After Extraction

Once images are downloaded:

1. **Review**: Check `data/images/` for downloaded images
2. **Verify**: Look at `data/image_list.csv` 
3. **Start annotating**:
   ```bash
   ./start.sh
   ```
4. **Open**: `frontend/index.html` in your browser

## Advanced: Using Excel files

If you prefer Excel format:

```bash
# Export from Google Sheets as .xlsx
python3 extract_images.py nest_data.xlsx -n 100
```

## Tips

- **Start small**: Use `-n 10` to test with 10 images first
- **Filter wisely**: Use `-f y` to focus on images with plastic
- **Re-run safe**: Script skips already downloaded images
- **Batch approach**: Download in batches (50-100 at a time)
- **Check quality**: Review downloaded images before annotating

## Notes

- Images are named with submission ID prefix for traceability
- Original plastic status is preserved in CSV for reference
- Download includes 0.5s delay between requests (server-friendly)
- Failed downloads are logged but don't stop the process
