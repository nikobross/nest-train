"""
Data Handler for reading image lists from spreadsheets
"""
import pandas as pd
from pathlib import Path
import os


class DataHandler:
    """Handles reading image data from CSV/Excel files"""
    
    def __init__(self, spreadsheet_path):
        """
        Initialize data handler
        
        Args:
            spreadsheet_path: Path to CSV or Excel file containing image information
        """
        self.spreadsheet_path = Path(spreadsheet_path)
        self.df = None
        self._load_data()
    
    def _load_data(self):
        """Load data from spreadsheet"""
        if not self.spreadsheet_path.exists():
            print(f"Warning: Spreadsheet not found at {self.spreadsheet_path}")
            print("Creating empty dataframe. Please add your data file.")
            self.df = pd.DataFrame(columns=['image_path', 'row', 'col'])
            return
        
        # Detect file type and load accordingly
        file_ext = self.spreadsheet_path.suffix.lower()
        
        if file_ext == '.csv':
            self.df = pd.read_csv(self.spreadsheet_path)
        elif file_ext in ['.xlsx', '.xls']:
            self.df = pd.read_excel(self.spreadsheet_path)
        else:
            raise ValueError(f"Unsupported file format: {file_ext}")
        
        # Validate required columns
        if 'image_path' not in self.df.columns:
            # Try to find the first column that looks like a path
            for col in self.df.columns:
                if any(ext in str(self.df[col].iloc[0]).lower() 
                       for ext in ['.jpg', '.jpeg', '.png'] if len(self.df) > 0):
                    self.df.rename(columns={col: 'image_path'}, inplace=True)
                    break
    
    def get_image_list(self):
        """
        Get list of all images
        
        Returns:
            List of dictionaries containing image information
        """
        if self.df is None or len(self.df) == 0:
            return []
        
        images = []
        for idx, row in self.df.iterrows():
            images.append({
                'index': int(idx),
                'path': str(row.get('image_path', '')),
                'row': int(row.get('row', idx)) if 'row' in row else int(idx),
                'col': str(row.get('col', 'A')) if 'col' in row else 'A',
                'filename': os.path.basename(str(row.get('image_path', '')))
            })
        
        return images
    
    def get_image_at_index(self, index):
        """Get image information at specific index"""
        if self.df is None or index >= len(self.df):
            return None
        
        row = self.df.iloc[index]
        return {
            'index': int(index),
            'path': str(row.get('image_path', '')),
            'row': int(row.get('row', index)) if 'row' in row else int(index),
            'col': str(row.get('col', 'A')) if 'col' in row else 'A',
            'filename': os.path.basename(str(row.get('image_path', '')))
        }
    
    def get_total_images(self):
        """Get total number of images"""
        return len(self.df) if self.df is not None else 0
