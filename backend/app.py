"""
Flask backend for Bird Nest Plastic Annotation Tool
Handles image serving, annotation storage, and progress tracking
"""
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import os
import json
from datetime import datetime
from utils.data_handler import DataHandler
from utils.annotation_handler import AnnotationHandler
from config import Config

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend communication

# Initialize handlers
data_handler = DataHandler(Config.DATA_SPREADSHEET_PATH)
annotation_handler = AnnotationHandler(Config.ANNOTATIONS_DIR, Config.PROGRESS_FILE)


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})


@app.route('/api/images/list', methods=['GET'])
def get_image_list():
    """Get list of all images from spreadsheet"""
    try:
        images = data_handler.get_image_list()
        return jsonify({
            'success': True,
            'images': images,
            'total': len(images)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/images/<path:filename>', methods=['GET'])
def serve_image(filename):
    """Serve image file"""
    try:
        return send_from_directory(Config.IMAGES_DIR, filename)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 404


@app.route('/api/progress', methods=['GET'])
def get_progress():
    """Get current annotation progress"""
    try:
        progress = annotation_handler.get_progress()
        return jsonify({
            'success': True,
            'progress': progress
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/progress', methods=['POST'])
def update_progress():
    """Update current annotation progress"""
    try:
        data = request.json
        current_index = data.get('current_index', 0)
        annotation_handler.save_progress(current_index)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/annotations/<int:image_index>', methods=['GET'])
def get_annotation(image_index):
    """Get annotation for specific image"""
    try:
        annotation = annotation_handler.get_annotation(image_index)
        return jsonify({
            'success': True,
            'annotation': annotation
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/annotations/<int:image_index>', methods=['POST'])
def save_annotation(image_index):
    """Save annotation for specific image"""
    try:
        data = request.json
        annotation_handler.save_annotation(image_index, data)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/annotations/export', methods=['GET'])
def export_annotations():
    """Export all annotations in ML-ready format"""
    try:
        annotations = annotation_handler.export_all_annotations()
        return jsonify({
            'success': True,
            'annotations': annotations,
            'format': 'COCO-style'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


if __name__ == '__main__':
    app.run(
        host=Config.HOST,
        port=Config.PORT,
        debug=Config.DEBUG
    )
