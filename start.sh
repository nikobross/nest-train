#!/bin/bash

# Bird Nest Plastic Annotation Tool - Startup Script
# This script sets up and starts the annotation tool

echo "🪹 Bird Nest Plastic Annotation Tool"
echo "===================================="
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    
    echo "📥 Installing dependencies..."
    source venv/bin/activate
    pip install -r backend/requirements.txt
else
    echo "✓ Virtual environment found"
    source venv/bin/activate
fi

echo ""
echo "🚀 Starting backend server..."
echo "   Server will run on http://localhost:5001"
echo ""
echo "📝 To use the tool:"
echo "   1. Open frontend/index.html in your web browser"
echo "   2. Or run: open frontend/index.html (macOS)"
echo ""
echo "⌨️  Press Ctrl+C to stop the server"
echo ""
echo "----------------------------------------"
echo ""

# Start the backend
cd backend
python app.py
