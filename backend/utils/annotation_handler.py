"""
Annotation Handler for managing bounding box annotations and progress
"""
import json
import os
from pathlib import Path
from datetime import datetime
import shutil


class AnnotationHandler:
    """Handles saving, loading, and exporting annotations"""
    
    def __init__(self, annotations_dir, progress_file):
        """
        Initialize annotation handler
        
        Args:
            annotations_dir: Directory to store annotation files
            progress_file: Path to progress tracking file
        """
        self.annotations_dir = Path(annotations_dir)
        self.progress_file = Path(progress_file)
        
        # Create directories if they don't exist
        self.annotations_dir.mkdir(parents=True, exist_ok=True)
        self.progress_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize progress file if it doesn't exist
        if not self.progress_file.exists():
            self._initialize_progress()
    
    def _initialize_progress(self):
        """Initialize progress file"""
        progress = {
            'current_index': 0,
            'last_updated': datetime.now().isoformat(),
            'total_annotated': 0
        }
        self._write_json(self.progress_file, progress)
    
    def get_progress(self):
        """Get current progress"""
        if not self.progress_file.exists():
            self._initialize_progress()
        return self._read_json(self.progress_file)
    
    def save_progress(self, current_index):
        """
        Save current progress
        
        Args:
            current_index: Current image index
        """
        progress = self.get_progress()
        progress['current_index'] = current_index
        progress['last_updated'] = datetime.now().isoformat()
        self._write_json(self.progress_file, progress)
    
    def get_annotation(self, image_index):
        """
        Get annotation for specific image
        
        Args:
            image_index: Index of the image
            
        Returns:
            Annotation data or None if not found
        """
        annotation_file = self.annotations_dir / f"annotation_{image_index:05d}.json"
        
        if not annotation_file.exists():
            return None
        
        return self._read_json(annotation_file)
    
    def save_annotation(self, image_index, annotation_data):
        """
        Save annotation for specific image
        
        Args:
            image_index: Index of the image
            annotation_data: Dictionary containing annotation information
        """
        annotation_file = self.annotations_dir / f"annotation_{image_index:05d}.json"
        
        # Add metadata
        annotation_data['image_index'] = image_index
        annotation_data['timestamp'] = datetime.now().isoformat()
        
        # Create backup if file exists
        if annotation_file.exists():
            backup_file = self.annotations_dir / f"annotation_{image_index:05d}.backup.json"
            shutil.copy2(annotation_file, backup_file)
        
        # Save annotation
        self._write_json(annotation_file, annotation_data)
        
        # Update progress
        progress = self.get_progress()
        annotated_count = len(list(self.annotations_dir.glob("annotation_*.json")))
        # Exclude backup files
        annotated_count = len([f for f in self.annotations_dir.glob("annotation_*.json") 
                              if 'backup' not in f.name])
        progress['total_annotated'] = annotated_count
        self._write_json(self.progress_file, progress)
    
    def export_all_annotations(self):
        """
        Export all annotations in COCO-style format
        Always saves to the same file (annotations_export.json)
        Creates backup of previous export before overwriting
        
        Returns:
            Dictionary containing all annotations
        """
        annotations = []
        
        # Get all annotation files (excluding backups)
        annotation_files = sorted([f for f in self.annotations_dir.glob("annotation_*.json") 
                                  if 'backup' not in f.name])
        
        for annotation_file in annotation_files:
            annotation = self._read_json(annotation_file)
            if annotation:
                annotations.append(annotation)
        
        export_data = {
            'annotations': annotations,
            'total': len(annotations),
            'exported_at': datetime.now().isoformat(),
            'format_version': '1.0'
        }
        
        # Use consistent filename
        export_file = self.annotations_dir.parent / "annotations_export.json"
        
        # Create backup of previous export if it exists
        if export_file.exists():
            backup_file = self.annotations_dir.parent / "annotations_export.backup.json"
            shutil.copy2(export_file, backup_file)
        
        # Save export file
        self._write_json(export_file, export_data)
        
        return export_data
    
    @staticmethod
    def _read_json(file_path):
        """Read JSON file"""
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return None
    
    @staticmethod
    def _write_json(file_path, data):
        """Write JSON file"""
        try:
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            print(f"Error writing {file_path}: {e}")
            return False
