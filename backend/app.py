"""
MinuteMate Flask Application
Main application file for the MinuteMate AI-powered meeting minutes generator.
"""

import os
import logging
from datetime import datetime
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge

# Import our custom modules
from config import get_config
from utils import (
    generate_job_id, validate_file_type, get_audio_video_mimes,
    ensure_directory_exists, create_response, format_file_size, get_file_size
)
from job_tracker import job_tracker, JobStatus

# Import processing modules (will be created next)
# from modules.transcriber import AudioTranscriber
# from modules.parser import MinutesParser
# from modules.formatter import MinutesFormatter
# from modules.exporter import DocxExporter
# from modules.user_profiles import UserProfileManager

def create_app():
    """Application factory pattern"""
    app = Flask(__name__)

    # Load configuration
    config_class = get_config()
    app.config.from_object(config_class)

    # Enable CORS for frontend integration
    CORS(app)

    # Setup logging
    logging.basicConfig(
        level=getattr(logging, app.config.get('LOG_LEVEL', 'INFO')),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Ensure required directories exist
    ensure_directory_exists(app.config['UPLOAD_FOLDER'])
    ensure_directory_exists(app.config['OUTPUT_FOLDER'])
    ensure_directory_exists(app.config.get('TEMP_FOLDER', 'temp'))
    ensure_directory_exists(os.path.dirname(app.config.get('LOG_FILE', 'logs/app.log')))

    return app

app = create_app()

def allowed_file(filename):
    """Check if uploaded file has an allowed extension"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def index():
    """Health check and API info endpoint"""
    return jsonify({
        'message': 'MinuteMate API is running',
        'version': '1.0.0',
        'status': 'healthy',
        'endpoints': {
            'upload': '/api/upload',
            'status': '/api/status/<job_id>',
            'download': '/api/download/<job_id>',
            'jobs': '/api/jobs',
            'health': '/'
        },
        'supported_formats': {
            'audio': list(app.config['ALLOWED_AUDIO_EXTENSIONS']),
            'video': list(app.config['ALLOWED_VIDEO_EXTENSIONS'])
        },
        'limits': {
            'max_file_size': f"{app.config['MAX_CONTENT_LENGTH'] // (1024*1024)}MB"
        }
    })

@app.route('/api/jobs', methods=['GET'])
def list_jobs():
    """List all jobs (for debugging/admin purposes)"""
    jobs = job_tracker.get_all_jobs()
    response = create_response(True, f'Retrieved {len(jobs)} jobs', {'jobs': jobs})
    return jsonify(response), 200

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Handle file upload for audio/video processing"""
    try:
        # Check if file is present in request
        if 'file' not in request.files:
            response = create_response(False, 'No file provided')
            return jsonify(response), 400

        file = request.files['file']

        # Check if file was selected
        if file.filename == '':
            response = create_response(False, 'No file selected')
            return jsonify(response), 400

        # Validate file extension
        if not allowed_file(file.filename):
            response = create_response(
                False,
                'Invalid file type',
                {'allowed_types': list(app.config['ALLOWED_EXTENSIONS'])}
            )
            return jsonify(response), 400

        # Generate secure filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        original_filename = secure_filename(file.filename)
        filename = f"{timestamp}_{original_filename}"

        # Save file
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        # Get file info
        file_size = get_file_size(file_path)
        formatted_size = format_file_size(file_size)

        # Validate file type using magic
        mimes = get_audio_video_mimes()
        all_allowed_mimes = mimes['audio'] | mimes['video']

        if not validate_file_type(file_path, all_allowed_mimes):
            os.remove(file_path)  # Clean up invalid file
            response = create_response(False, 'Invalid file format detected')
            return jsonify(response), 400

        # Generate job ID for tracking
        job_id = generate_job_id(original_filename)

        # Create job entry in tracker
        job_info = job_tracker.create_job(job_id, original_filename, formatted_size)

        app.logger.info(f"File uploaded successfully: {filename}, Job ID: {job_id}, Size: {formatted_size}")

        # TODO: Start background processing task
        # This is where we'll integrate the transcription pipeline

        response = create_response(
            True,
            'File uploaded successfully',
            {
                'job_id': job_id,
                'filename': original_filename,
                'file_size': formatted_size,
                'status': job_info['status'],
                'next_step': 'transcription'
            }
        )
        return jsonify(response), 200

    except RequestEntityTooLarge:
        max_size_mb = app.config['MAX_CONTENT_LENGTH'] // (1024*1024)
        response = create_response(
            False,
            f'File too large. Maximum size allowed: {max_size_mb}MB'
        )
        return jsonify(response), 413
    except Exception as e:
        app.logger.error(f"Upload error: {str(e)}")
        response = create_response(False, 'Internal server error')
        return jsonify(response), 500

@app.route('/api/status/<job_id>', methods=['GET'])
def get_job_status(job_id):
    """Get processing status for a job"""
    job_info = job_tracker.get_job(job_id)

    if not job_info:
        response = create_response(False, 'Job not found')
        return jsonify(response), 404

    response = create_response(True, 'Job status retrieved', job_info)
    return jsonify(response), 200

@app.route('/api/download/<job_id>', methods=['GET'])
def download_result(job_id):
    """Download processed meeting minutes"""
    job_info = job_tracker.get_job(job_id)

    if not job_info:
        response = create_response(False, 'Job not found')
        return jsonify(response), 404

    if job_info['status'] != JobStatus.COMPLETED.value:
        response = create_response(
            False,
            f"Job not completed. Current status: {job_info['status']}"
        )
        return jsonify(response), 400

    if not job_info.get('result_file') or not os.path.exists(job_info['result_file']):
        response = create_response(False, 'Result file not found')
        return jsonify(response), 404

    try:
        return send_file(
            job_info['result_file'],
            as_attachment=True,
            download_name=f"minutes_{job_info['filename']}.docx"
        )
    except Exception as e:
        app.logger.error(f"Download error for job {job_id}: {str(e)}")
        response = create_response(False, 'Error downloading file')
        return jsonify(response), 500

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    app.logger.error(f"Internal error: {str(error)}")
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # Development server
    app.run(debug=True, host='0.0.0.0', port=5000)