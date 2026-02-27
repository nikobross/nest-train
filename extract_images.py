"""
Google Spreadsheet Image Extractor
Extracts images from a Google Spreadsheet export and prepares them for annotation
"""
import pandas as pd
import requests
import os
from pathlib import Path
import csv
from urllib.parse import urlparse
import time
from typing import Optional

# Configuration
PROJECT_ROOT = Path(__file__).parent
IMAGES_DIR = PROJECT_ROOT / 'data' / 'images'
OUTPUT_CSV = PROJECT_ROOT / 'data' / 'image_list.csv'

# Column names from your spreadsheet
COL_SUB_ID = 'sub_id'
COL_IMAGE_URL = 'list'
COL_PLASTIC = 'Anthropogenic materials present? u=unsure (bad picture)   n=No  y=Yes'


class ImageExtractor:
    def __init__(self, spreadsheet_path, max_images=None, filter_plastic=None):
        """
        Initialize the image extractor
        
        Args:
            spreadsheet_path: Path to exported spreadsheet (CSV or Excel)
            max_images: Maximum number of images to download (None = all)
            filter_plastic: Filter by plastic presence ('y', 'n', 'u', or None for all)
        """
        self.spreadsheet_path = Path(spreadsheet_path)
        self.max_images = max_images
        self.filter_plastic = filter_plastic
        self.df = None
        self.downloaded = []
        
        # Ensure images directory exists
        IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    
    def load_spreadsheet(self):
        """Load the spreadsheet data"""
        print(f"📊 Loading spreadsheet: {self.spreadsheet_path}")
        
        file_ext = self.spreadsheet_path.suffix.lower()
        
        try:
            if file_ext == '.tsv':
                # Tab-separated values
                self.df = pd.read_csv(self.spreadsheet_path, sep='\t')
            elif file_ext == '.csv':
                # Try different separators
                self.df = pd.read_csv(self.spreadsheet_path, sep='\t')
                if len(self.df.columns) == 1:
                    self.df = pd.read_csv(self.spreadsheet_path)
            elif file_ext in ['.xlsx', '.xls']:
                self.df = pd.read_excel(self.spreadsheet_path)
            else:
                raise ValueError(f"Unsupported file format: {file_ext}. Supported: .tsv, .csv, .xlsx, .xls")
            
            print(f"✓ Loaded {len(self.df)} rows")
            print(f"✓ Columns: {len(self.df.columns)}")
            
            # Verify required columns exist
            if COL_IMAGE_URL not in self.df.columns:
                print(f"\n⚠️  Warning: '{COL_IMAGE_URL}' column not found")
                print(f"Available columns: {list(self.df.columns)}")
                return False
            
            return True
            
        except Exception as e:
            print(f"❌ Error loading spreadsheet: {e}")
            return False
    
    def filter_data(self):
        """Filter data based on criteria"""
        original_count = len(self.df)
        
        # Filter out rows without image URLs
        self.df = self.df[self.df[COL_IMAGE_URL].notna()]
        self.df = self.df[self.df[COL_IMAGE_URL].str.startswith('http', na=False)]
        
        print(f"✓ Found {len(self.df)} rows with valid image URLs")
        
        # Filter by plastic presence if specified
        if self.filter_plastic and COL_PLASTIC in self.df.columns:
            self.df = self.df[self.df[COL_PLASTIC] == self.filter_plastic]
            print(f"✓ Filtered to {len(self.df)} images with plastic='{self.filter_plastic}'")
        
        # Limit number of images if specified
        if self.max_images:
            self.df = self.df.head(self.max_images)
            print(f"✓ Limited to {len(self.df)} images")
        
        return len(self.df)
    
    def download_image(self, url, filename):
        """
        Download a single image
        
        Args:
            url: Image URL
            filename: Local filename to save
            
        Returns:
            True if successful, False otherwise
        """
        try:
            response = requests.get(url, timeout=30, stream=True)
            response.raise_for_status()
            
            filepath = IMAGES_DIR / filename
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            return True
            
        except Exception as e:
            print(f"  ❌ Failed: {e}")
            return False
    
    def extract_filename(self, url, sub_id):
        """
        Extract or generate filename from URL
        
        Args:
            url: Image URL
            sub_id: Submission ID for fallback naming
            
        Returns:
            Filename string
        """
        # Try to get filename from URL
        parsed = urlparse(url)
        path = parsed.path
        
        if path:
            # Get the last part of the path
            original_name = Path(path).name
            
            # If it has an extension, use it
            if '.' in original_name:
                # Add sub_id prefix for uniqueness
                name, ext = os.path.splitext(original_name)
                return f"{sub_id}_{original_name}"
        
        # Fallback: use sub_id with .jpeg extension
        return f"{sub_id}.jpeg"
    
    def download_images(self):
        """Download all filtered images"""
        total = len(self.df)
        print(f"\n📥 Downloading {total} images...")
        print("=" * 50)
        
        for idx, row in self.df.iterrows():
            url = row[COL_IMAGE_URL]
            sub_id = row[COL_SUB_ID] if COL_SUB_ID in row else f"img_{idx}"
            
            filename = self.extract_filename(url, sub_id)
            filepath = IMAGES_DIR / filename
            
            # Skip if already exists
            if filepath.exists():
                print(f"[{len(self.downloaded) + 1}/{total}] ⏭️  Skipped (exists): {filename}")
                self.downloaded.append({
                    'filename': filename,
                    'sub_id': sub_id,
                    'url': url,
                    'row': row,
                    'downloaded': False
                })
                continue
            
            print(f"[{len(self.downloaded) + 1}/{total}] ⬇️  Downloading: {filename}")
            
            success = self.download_image(url, filename)
            
            if success:
                print(f"  ✓ Saved to: {filepath}")
                self.downloaded.append({
                    'filename': filename,
                    'sub_id': sub_id,
                    'url': url,
                    'row': row,
                    'downloaded': True
                })
            else:
                self.downloaded.append({
                    'filename': filename,
                    'sub_id': sub_id,
                    'url': url,
                    'row': row,
                    'downloaded': False
                })
            
            # Be nice to the server
            time.sleep(0.5)
        
        successful = sum(1 for item in self.downloaded if item['downloaded'] or 
                        (IMAGES_DIR / item['filename']).exists())
        print(f"\n✓ Successfully downloaded/found {successful}/{total} images")
        
        return successful
    
    def create_csv(self):
        """Create image_list.csv for the annotation tool"""
        print(f"\n📝 Creating {OUTPUT_CSV}...")
        
        csv_data = []
        
        for idx, item in enumerate(self.downloaded):
            row_data = item['row']
            
            csv_row = {
                'image_path': item['filename'],
                'row': idx,
                'col': 'A',
                'sub_id': item['sub_id'],
                'url': item['url']
            }
            
            # Add plastic status if available
            if COL_PLASTIC in row_data:
                plastic_status = row_data[COL_PLASTIC]
                csv_row['has_plastic_initial'] = plastic_status
                csv_row['notes'] = f"Original: {plastic_status} (y=Yes, n=No, u=Unsure)"
            
            csv_data.append(csv_row)
        
        # Write CSV
        df_output = pd.DataFrame(csv_data)
        df_output.to_csv(OUTPUT_CSV, index=False)
        
        print(f"✓ Created CSV with {len(csv_data)} entries")
        print(f"✓ Location: {OUTPUT_CSV}")
        
        # Show preview
        print("\n📋 CSV Preview (first 5 rows):")
        print(df_output.head().to_string())
    
    def run(self):
        """Run the complete extraction process"""
        print("🪹 Bird Nest Image Extractor")
        print("=" * 50)
        print()
        
        # Load spreadsheet
        if not self.load_spreadsheet():
            return False
        
        # Filter data
        count = self.filter_data()
        if count == 0:
            print("❌ No images to download after filtering")
            return False
        
        # Confirm with user
        print(f"\n⚠️  About to download {count} images")
        print(f"   Destination: {IMAGES_DIR}")
        
        # Download images
        self.download_images()
        
        # Create CSV
        self.create_csv()
        
        print("\n" + "=" * 50)
        print("✅ Extraction complete!")
        print("\n📋 Next steps:")
        print("   1. Review the downloaded images in data/images/")
        print("   2. Check data/image_list.csv")
        print("   3. Run: ./start.sh")
        print("   4. Open frontend/index.html in your browser")
        
        return True


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Extract images from Google Spreadsheet export for annotation'
    )
    parser.add_argument(
        'spreadsheet',
        help='Path to exported spreadsheet file (CSV or Excel)'
    )
    parser.add_argument(
        '-n', '--max-images',
        type=int,
        default=None,
        help='Maximum number of images to download (default: all)'
    )
    parser.add_argument(
        '-f', '--filter-plastic',
        choices=['y', 'n', 'u'],
        default=None,
        help='Filter by plastic presence: y=Yes, n=No, u=Unsure (default: all)'
    )
    parser.add_argument(
        '--skip-download',
        action='store_true',
        help='Skip download step, only create CSV from existing images'
    )
    
    args = parser.parse_args()
    
    # Check if spreadsheet exists
    if not Path(args.spreadsheet).exists():
        print(f"❌ Spreadsheet not found: {args.spreadsheet}")
        print("\n💡 How to export from Google Sheets:")
        print("   1. Open your Google Spreadsheet")
        print("   2. File → Download → Tab-separated values (.tsv)")
        print("   3. Save to this project directory")
        print("   4. Run this script again with the downloaded file")
        return
    
    # Create extractor and run
    extractor = ImageExtractor(
        spreadsheet_path=args.spreadsheet,
        max_images=args.max_images,
        filter_plastic=args.filter_plastic
    )
    
    extractor.run()


if __name__ == '__main__':
    main()
