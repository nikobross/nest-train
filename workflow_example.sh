#!/bin/bash

# Example Workflow: Extract and Start Annotating
# This script demonstrates the complete workflow from Google Sheets to annotation

echo "🪹 Bird Nest Annotation - Complete Workflow Example"
echo "===================================================="
echo ""

# Check if spreadsheet file is provided
if [ $# -eq 0 ]; then
    echo "Usage: ./workflow_example.sh <spreadsheet_file.tsv> [max_images]"
    echo ""
    echo "Example:"
    echo "  ./workflow_example.sh nest_data.tsv 50"
    echo ""
    echo "Steps to prepare:"
    echo "  1. Open your Google Spreadsheet"
    echo "  2. File → Download → Tab-separated values (.tsv)"
    echo "  3. Save to this directory"
    echo "  4. Run this script with the filename"
    echo ""
    exit 1
fi

SPREADSHEET=$1
MAX_IMAGES=${2:-50}  # Default to 50 if not specified

# Check if file exists
if [ ! -f "$SPREADSHEET" ]; then
    echo "❌ File not found: $SPREADSHEET"
    exit 1
fi

echo "📋 Configuration:"
echo "   Spreadsheet: $SPREADSHEET"
echo "   Max images: $MAX_IMAGES"
echo ""

# Step 1: Setup environment
echo "=== Step 1: Setting up environment ==="
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate
echo "Installing/updating dependencies..."
pip install -q -r backend/requirements.txt
echo "✓ Environment ready"
echo ""

# Step 2: Extract images
echo "=== Step 2: Extracting images from spreadsheet ==="
echo "This will download $MAX_IMAGES images..."
read -p "Continue? (y/n): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    python3 extract_images.py "$SPREADSHEET" -n "$MAX_IMAGES"
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "✓ Image extraction complete!"
    else
        echo "❌ Extraction failed. Please check the errors above."
        exit 1
    fi
else
    echo "Skipping extraction..."
fi

echo ""

# Step 3: Ask if user wants to start annotation
echo "=== Step 3: Ready to start annotation ==="
echo ""
echo "Next steps:"
echo "  1. Backend server will start on http://localhost:5001"
echo "  2. Open frontend/index.html in your browser"
echo "  3. Start annotating!"
echo ""
read -p "Start the annotation server now? (y/n): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "🚀 Starting backend server..."
    echo "   Press Ctrl+C to stop"
    echo ""
    echo "📝 Then open: frontend/index.html"
    echo ""
    echo "----------------------------------------"
    echo ""
    
    cd backend
    python app.py
else
    echo ""
    echo "To start the server later, run:"
    echo "  ./start.sh"
    echo ""
    echo "Or manually:"
    echo "  cd backend && python app.py"
    echo ""
fi
