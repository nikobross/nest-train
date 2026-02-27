"""
Data Preparation Helper Script
This script helps you prepare your image list CSV from a directory of images
"""
import os
import csv
from pathlib import Path

# Configuration
IMAGES_DIR = Path(__file__).parent / 'data' / 'images'
OUTPUT_CSV = Path(__file__).parent / 'data' / 'image_list.csv'
SUPPORTED_FORMATS = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.JPG', '.JPEG', '.PNG']


def find_images(directory):
    """Find all image files in the directory"""
    images = []
    
    for file in directory.iterdir():
        if file.is_file() and file.suffix in SUPPORTED_FORMATS:
            images.append(file.name)
    
    return sorted(images)


def create_csv(images, output_path):
    """Create CSV file with image list"""
    with open(output_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['image_path', 'row', 'col'])
        
        for idx, image in enumerate(images, start=1):
            writer.writerow([image, idx, 'A'])
    
    print(f"✓ Created {output_path}")
    print(f"✓ Found {len(images)} images")


def main():
    print("🪹 Bird Nest Annotation - Data Preparation")
    print("=" * 50)
    print()
    
    # Check if images directory exists
    if not IMAGES_DIR.exists():
        print(f"❌ Images directory not found: {IMAGES_DIR}")
        print("   Please create the directory and add your images")
        return
    
    # Find images
    print(f"📁 Scanning: {IMAGES_DIR}")
    images = find_images(IMAGES_DIR)
    
    if not images:
        print("❌ No images found")
        print(f"   Supported formats: {', '.join(SUPPORTED_FORMATS)}")
        return
    
    print(f"✓ Found {len(images)} images")
    print()
    
    # Show sample
    print("Sample images:")
    for img in images[:5]:
        print(f"  • {img}")
    if len(images) > 5:
        print(f"  ... and {len(images) - 5} more")
    print()
    
    # Ask for confirmation
    response = input(f"Create CSV file at {OUTPUT_CSV}? (y/n): ")
    
    if response.lower() == 'y':
        create_csv(images, OUTPUT_CSV)
        print()
        print("✓ Data preparation complete!")
        print("  Next steps:")
        print("  1. Review the CSV file if needed")
        print("  2. Run: ./start.sh (or python backend/app.py)")
        print("  3. Open frontend/index.html in your browser")
    else:
        print("Cancelled")


if __name__ == '__main__':
    main()
