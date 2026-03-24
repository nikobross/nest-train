"""
Configuration settings for the annotation tool
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

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
    DEBUG = os.getenv('DEBUG', 'true').lower() == 'true'
    FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:8000')
    CORS_ORIGINS = [origin.strip() for origin in os.getenv(
        'CORS_ORIGINS',
        'http://localhost:8000,http://127.0.0.1:8000,null'
    ).split(',') if origin.strip()]
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'dev-only-change-me')
    
    # Paths
    DATA_DIR = DATA_DIR
    IMAGES_DIR = IMAGES_DIR
    ANNOTATIONS_DIR = ANNOTATIONS_DIR
    DATA_SPREADSHEET_PATH = DATA_SPREADSHEET_PATH
    PROGRESS_FILE = PROGRESS_FILE
    
    # Annotation settings
    AUTO_SAVE = True
    BACKUP_ENABLED = True

    # Google OAuth Configuration
    GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID', '')
    GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET', '')
    GOOGLE_REDIRECT_URI = os.getenv(
        'GOOGLE_REDIRECT_URI',
        f'http://localhost:{PORT}/api/auth/google-callback'
    )
    GOOGLE_SHEETS_SCOPE = 'https://www.googleapis.com/auth/spreadsheets'

    # Sheets integration settings
    SHEETS_IMAGE_COLUMN = 'list'
    SHEETS_HAS_PLASTIC_COLUMN = 'has_plastic'
    SHEETS_LOCATION_COLUMN = 'plastic_location_labels'
    SHEETS_LAST_INDEX_COLUMN = 'last_annotated_index'
    
    # Supported image formats
    SUPPORTED_FORMATS = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']
    
    @classmethod
    def validate_oauth_config(cls):
        """Validate OAuth environment variables on startup."""
        missing = []
        if not cls.GOOGLE_CLIENT_ID:
            missing.append('GOOGLE_CLIENT_ID')
        if not cls.GOOGLE_CLIENT_SECRET:
            missing.append('GOOGLE_CLIENT_SECRET')
        
        print(f'\n=== Google OAuth Configuration ===' , file=sys.stderr)
        print(f'GOOGLE_CLIENT_ID: {"✓ set" if cls.GOOGLE_CLIENT_ID else "✗ MISSING"}'  , file=sys.stderr)
        print(f'GOOGLE_CLIENT_SECRET: {"✓ set" if cls.GOOGLE_CLIENT_SECRET else "✗ MISSING"}', file=sys.stderr)
        print(f'GOOGLE_REDIRECT_URI: {cls.GOOGLE_REDIRECT_URI}', file=sys.stderr)
        print(f'FLASK_SECRET_KEY: {"✓ set" if os.getenv("FLASK_SECRET_KEY") else "⚠ using dev default"}', file=sys.stderr)
        print('====================================\n', file=sys.stderr)
        
        if missing:
            missing_str = ', '.join(missing)
            error_msg = f'Missing OAuth environment variables: {missing_str}. Please set these in .env or environment.'
            print(f'ERROR: {error_msg}', file=sys.stderr)
            return False
        return True
