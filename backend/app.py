"""
MinuteMate Flask Application
Main application file for the MinuteMate AI-powered meeting minutes generator.
"""

import os
import logging
import time
from datetime import datetime
from flask import Flask, request, jsonify, send_file, g
from flask_cors import CORS
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge

# Import our custom modules
from config import get_config
from utils import (
    generate_job_id, ensure_directory_exists, create_response, format_file_size
)
from job_tracker import job_tracker, JobStatus
from file_manager import FileStorageManager, FileValidationError, FileStorageError
from scheduler import create_cleanup_scheduler
from logging_config import setup_logging
from error_handlers import ErrorHandler, ValidationError, FileProcessingError, SecurityError
from middleware import setup_middleware, health_monitor

# Import processing modules (will be created next)
# from modules.transcriber import AudioTranscriber
# from modules.parser import MinutesParser
# from modules.formatter import MinutesFormatter
# from modules.exporter import DocxExporter
# from modules.user_profiles import UserProfileManager

def create_app():
    """Application factory pattern with enhanced error handling and logging"""
    app = Flask(__name__)

    # Load configuration
    config_class = get_config()
    app.config.from_object(config_class)

    # Setup enhanced logging first
    logging_manager = setup_logging(app.config)
    app.logging_manager = logging_manager

    # Enable CORS for frontend integration
    CORS(app)

    # Setup error handling
    error_handler = ErrorHandler(app)
    app.error_handler = error_handler

    # Setup middleware for request logging and monitoring
    middleware = setup_middleware(app)
    app.middleware = middleware

    # Ensure required directories exist
    ensure_directory_exists(app.config['UPLOAD_FOLDER'])
    ensure_directory_exists(app.config['OUTPUT_FOLDER'])
    ensure_directory_exists(app.config.get('TEMP_FOLDER', 'temp'))
    ensure_directory_exists(app.config.get('LOG_DIR', 'logs'))

    # Log application startup
    logger = logging.getLogger(__name__)
    logger.info("MinuteMate application initialized successfully")

    return app

app = create_app()

# Initialize file storage manager
file_storage = FileStorageManager(
    base_upload_dir=app.config['UPLOAD_FOLDER'],
    base_output_dir=app.config['OUTPUT_FOLDER'],
    temp_dir=app.config['TEMP_FOLDER']
)

# Initialize cleanup scheduler
cleanup_scheduler = create_cleanup_scheduler(file_storage, job_tracker, app.config)
cleanup_scheduler.start()

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
            'file_info': '/api/files/info/<job_id>',
            'cleanup': '/api/files/cleanup',
            'health': '/',
            'detailed_health': '/api/health/detailed',
            'monitoring_dashboard': '/api/monitoring/dashboard'
        },
        'supported_formats': {
            'audio': list(app.config['ALLOWED_AUDIO_EXTENSIONS']),
            'video': list(app.config['ALLOWED_VIDEO_EXTENSIONS'])
        },
        'limits': {
            'max_file_size': f"{app.config['MAX_CONTENT_LENGTH'] // (1024*1024)}MB",
            'max_filename_length': app.config.get('MAX_FILENAME_LENGTH', 255)
        },
        'security_features': {
            'mime_validation': app.config.get('ENABLE_MIME_VALIDATION', True),
            'malicious_scan': app.config.get('ENABLE_MALICIOUS_SCAN', True),
            'file_organization': app.config.get('ORGANIZE_BY_TYPE', True)
        },
        'storage_info': {
            'upload_folder': app.config['UPLOAD_FOLDER'],
            'auto_cleanup': app.config.get('AUTO_CLEANUP_ENABLED', True),
            'max_file_age_hours': app.config.get('MAX_FILE_AGE_HOURS', 24)
        }
    })

@app.route('/api/jobs', methods=['GET'])
def list_jobs():
    """List all jobs (for debugging/admin purposes)"""
    jobs = job_tracker.get_all_jobs()
    response = create_response(True, f'Retrieved {len(jobs)} jobs', {'jobs': jobs})
    return jsonify(response), 200

@app.route('/api/files/cleanup', methods=['POST'])
def cleanup_files():
    """Clean up old files (admin endpoint)"""
    try:
        # Get max age from request or use default
        data = request.get_json() or {}
        max_age_hours = data.get('max_age_hours', app.config.get('MAX_FILE_AGE_HOURS', 24))

        # Run manual cleanup using scheduler
        cleanup_stats = cleanup_scheduler.run_manual_cleanup(max_age_hours)

        response = create_response(
            True,
            'Cleanup completed successfully',
            cleanup_stats
        )
        return jsonify(response), 200

    except Exception as e:
        app.logger.error(f"Cleanup error: {str(e)}")
        response = create_response(False, 'Cleanup failed')
        return jsonify(response), 500

@app.route('/api/files/info/<job_id>', methods=['GET'])
def get_file_info(job_id):
    """Get information about a file associated with a job"""
    logger = logging.getLogger(__name__)

    try:
        job_info = job_tracker.get_job(job_id)
        if not job_info:
            raise ValidationError('Job not found', field='job_id', value=job_id)

        response = create_response(True, 'File info retrieved', job_info)
        return jsonify(response), 200

    except ValidationError:
        raise
    except Exception as e:
        logger.error(f"File info error: {str(e)}", exc_info=True)
        raise

@app.route('/api/monitoring/dashboard', methods=['GET'])
def monitoring_dashboard():
    """Get comprehensive monitoring dashboard data"""
    logger = logging.getLogger(__name__)

    try:
        # Get health metrics
        health_status = health_monitor.get_health_status()

        # Get job statistics
        all_jobs = job_tracker.get_all_jobs()
        job_stats = {
            'total_jobs': len(all_jobs),
            'completed_jobs': len([j for j in all_jobs.values() if j['status'] == 'completed']),
            'failed_jobs': len([j for j in all_jobs.values() if j['status'] == 'failed']),
            'in_progress_jobs': len([j for j in all_jobs.values() if j['status'] in ['uploaded', 'transcribing', 'parsing', 'formatting', 'exporting']])
        }

        # System information
        import psutil
        system_info = {
            'cpu_percent': psutil.cpu_percent(),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_usage': psutil.disk_usage('/').percent
        }

        dashboard_data = {
            'health': health_status,
            'jobs': job_stats,
            'system': system_info,
            'timestamp': datetime.now().isoformat()
        }

        response = create_response(True, 'Dashboard data retrieved', dashboard_data)
        return jsonify(response), 200

    except Exception as e:
        logger.error(f"Dashboard error: {str(e)}", exc_info=True)
        # Return basic health info even if detailed monitoring fails
        basic_health = health_monitor.get_health_status()
        response = create_response(True, 'Basic dashboard data retrieved', {'health': basic_health})
        return jsonify(response), 200

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Handle file upload for audio/video processing with enhanced validation"""
    logger = logging.getLogger(__name__)

    try:
        # Check if file is present in request
        if 'file' not in request.files:
            raise ValidationError('No file provided', field='file')

        file = request.files['file']

        # Check if file was selected
        if file.filename == '':
            raise ValidationError('No file selected', field='file')

        # Basic extension check (quick validation)
        if not allowed_file(file.filename):
            raise ValidationError(
                'Invalid file type',
                field='file',
                value=file.filename
            )

        # Generate job ID for tracking
        job_id = generate_job_id(file.filename)

        # Use enhanced file storage manager
        storage_result = file_storage.store_uploaded_file(
            uploaded_file=file,
            original_filename=file.filename,
            job_id=job_id,
            max_size_bytes=app.config['MAX_CONTENT_LENGTH']
        )

        if not storage_result['success']:
            raise FileProcessingError(
                storage_result['error'],
                operation='file_storage'
            )

        # Get file information
        file_info = storage_result['file_info']
        formatted_size = format_file_size(file_info['size_bytes'])

        # Create job entry in tracker with enhanced info
        job_info = job_tracker.create_job(
            job_id=job_id,
            filename=file.filename,
            file_size=formatted_size,
            file_path=storage_result['file_path'],
            file_type=file_info['file_type']
        )

        # Add file storage info to job
        job_tracker.update_job(
            job_id,
            message=f"File uploaded and validated successfully. Type: {file_info['file_type']}"
        )

        app.logger.info(
            f"File uploaded successfully: {storage_result['secure_filename']}, "
            f"Job ID: {job_id}, Size: {formatted_size}, Type: {file_info['file_type']}"
        )

        # Prepare response data
        response_data = {
            'job_id': job_id,
            'filename': file.filename,
            'secure_filename': storage_result['secure_filename'],
            'file_size': formatted_size,
            'file_type': file_info['file_type'],
            'mime_type': file_info['mime_type'],
            'status': job_info['status'],
            'next_step': 'transcription'
        }

        # Include warnings if any
        if storage_result.get('warnings'):
            response_data['warnings'] = storage_result['warnings']

        # Record successful request
        health_monitor.record_request(True, time.time() - g.start_time)

        response = create_response(True, 'File uploaded successfully', response_data)
        return jsonify(response), 200

    except (ValidationError, FileProcessingError, SecurityError):
        # These are handled by the error handler
        health_monitor.record_request(False, time.time() - g.start_time)
        raise
    except RequestEntityTooLarge:
        health_monitor.record_request(False, time.time() - g.start_time, 'File too large')
        # This will be handled by the error handler
        raise
    except Exception as e:
        health_monitor.record_request(False, time.time() - g.start_time, str(e))
        logger.error(f"Unexpected upload error: {str(e)}", exc_info=True)
        raise

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

# Error handlers are now managed by the ErrorHandler class

if __name__ == '__main__':
    # Development server
    app.run(debug=True, host='0.0.0.0', port=5000)