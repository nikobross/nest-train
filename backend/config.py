"""
Configuration settings for the annotation tool
"""
import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).parent.parent

# Data directories
DATA_DIR = BASE_DIR / 'data'
IMAGES_DIR = DATA_DIR / 'images'
ANNOTATIONS_DIR = DATA_DIR / 'annotations'

# Spreadsheet path (update this with your actual spreadsheet file)
DATA_SPREADSHEET_PATH = DATA_DIR / 'image_list.csv'

# Progress tracking file
PROGRESS_FILE = DATA_DIR / 'progress.json'

# Server configuration
class Config:
    HOST = '0.0.0.0'
    PORT = 5001  # Changed from 5000 to avoid macOS AirPlay Receiver conflict
    DEBUG = True
    
    # Paths
    DATA_DIR = DATA_DIR
    IMAGES_DIR = IMAGES_DIR
    ANNOTATIONS_DIR = ANNOTATIONS_DIR
    DATA_SPREADSHEET_PATH = DATA_SPREADSHEET_PATH
    PROGRESS_FILE = PROGRESS_FILE
    
    # Annotation settings
    AUTO_SAVE = True
    BACKUP_ENABLED = True
    
    # Supported image formats
    SUPPORTED_FORMATS = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']
