"""
BoardMinutes Flask Application
Main application file for the BoardMinutes AI-powered board meeting minutes generator.
"""

import os
import logging
import time
import requests
import tempfile
from datetime import datetime, timezone
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
from flask import Flask, request, jsonify, send_file, g, send_from_directory
from flask_cors import CORS
from flask_login import LoginManager, login_required, current_user
from flask_jwt_extended import JWTManager
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge
from urllib.parse import urlparse
from pathlib import Path

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
from mock_processor import get_mock_processor

# Authentication imports
try:
    from models import db, User
    from auth_service import AuthService
    from auth_routes import auth_bp
    from meeting_service import MeetingService
    from meeting_routes import meeting_bp
    from template_service import TemplateService
    from template_routes import template_bp
    from calendar_service import CalendarService
    from calendar_routes import calendar_bp
    from batch_service import batch_processor
    from batch_routes import batch_bp
    from profile_routes import profile_bp
    from document_comparison_routes import doc_comparison_bp
    # Try to import technical improvements (graceful fallback if not available)
    try:
        from security_middleware import init_security, create_redis_client
        SECURITY_AVAILABLE = True
    except ImportError as e:
        print(f"Security middleware not available: {e}")
        SECURITY_AVAILABLE = False

    try:
        from performance_optimizer import init_performance_optimization, setup_database_optimizations
        PERFORMANCE_AVAILABLE = True
    except ImportError as e:
        print(f"Performance optimizer not available: {e}")
        PERFORMANCE_AVAILABLE = False

    try:
        from database_optimizer import optimize_database, get_database_health
        DATABASE_OPTIMIZER_AVAILABLE = True
    except ImportError as e:
        print(f"Database optimizer not available: {e}")
        DATABASE_OPTIMIZER_AVAILABLE = False

    try:
        from api_documentation import add_documentation_endpoints
        DOCS_AVAILABLE = True
    except ImportError as e:
        print(f"API documentation not available: {e}")
        DOCS_AVAILABLE = False

    AUTH_AVAILABLE = True
except ImportError as e:
    print(f"Authentication modules not available: {e}")
    AUTH_AVAILABLE = False
from ai_processor import AIProcessor
from document_generator import DocumentGenerator

# Import processing modules (will be created next)
# from modules.transcriber import AudioTranscriber
# from modules.parser import MinutesParser
# from modules.formatter import MinutesFormatter
# from modules.exporter import DocxExporter
# from modules.user_profiles import UserProfileManager

def create_app():
    """Application factory pattern with enhanced error handling and logging"""
    app = Flask(__name__)

    # Set development environment variables
    os.environ.setdefault('DISABLE_RATE_LIMITING', 'true')  # Disable rate limiting for development

    # Load configuration
    config_class = get_config()
    app.config.from_object(config_class)

    # Setup enhanced logging first
    logging_manager = setup_logging(app.config)
    app.logging_manager = logging_manager

    # Enable CORS for frontend integration
    CORS(app)

    # Setup authentication if available
    if AUTH_AVAILABLE:
        # Database setup - Railway provides DATABASE_URL
        database_url = os.environ.get('DATABASE_URL')
        if database_url and database_url.startswith('postgres://'):
            # Fix for Railway's postgres:// URL (should be postgresql://)
            database_url = database_url.replace('postgres://', 'postgresql://', 1)

        if database_url:
            app.config['SQLALCHEMY_DATABASE_URI'] = database_url
        else:
            db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'minutemate.db')
            app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'

        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        db.init_app(app)

        # Login manager setup
        login_manager = LoginManager()
        login_manager.init_app(app)
        login_manager.login_view = 'auth.login'
        login_manager.login_message = 'Please log in to access this page.'

        @login_manager.user_loader
        def load_user(user_id):
            return User.query.get(user_id)

        # JWT setup
        app.config['JWT_SECRET_KEY'] = app.config.get('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
        jwt = JWTManager(app)

        # Register authentication blueprint
        app.register_blueprint(auth_bp)

        # Register meeting blueprint
        app.register_blueprint(meeting_bp)

        # Register template blueprint
        app.register_blueprint(template_bp)

        # Register calendar blueprint
        app.register_blueprint(calendar_bp)

        # Register batch blueprint
        app.register_blueprint(batch_bp)

        # Register profile blueprint
        app.register_blueprint(profile_bp)

        # Register document comparison blueprint
        app.register_blueprint(doc_comparison_bp)

        # Initialize technical improvements if available
        if SECURITY_AVAILABLE:
            try:
                redis_client = create_redis_client()
                init_security(app)
                app.logger.info("Security middleware initialized")
            except Exception as e:
                app.logger.warning(f"Security middleware initialization failed: {e}")

        if PERFORMANCE_AVAILABLE:
            try:
                redis_client = redis_client if SECURITY_AVAILABLE else None
                init_performance_optimization(app, redis_client)
                app.logger.info("Performance optimization initialized")
            except Exception as e:
                app.logger.warning(f"Performance optimization initialization failed: {e}")

        # Create database tables
        with app.app_context():
            try:
                db.create_all()

                # Set up database optimizations if available
                if PERFORMANCE_AVAILABLE:
                    try:
                        setup_database_optimizations(db)
                        app.logger.info("Database performance optimizations applied")
                    except Exception as e:
                        app.logger.warning(f"Database performance optimization failed: {e}")

                if DATABASE_OPTIMIZER_AVAILABLE:
                    try:
                        optimize_database(app, db.engine)
                        app.logger.info("Database optimizer applied")
                    except Exception as e:
                        app.logger.warning(f"Database optimizer failed: {e}")

                app.logger.info(f"Database tables created successfully at: {app.config['SQLALCHEMY_DATABASE_URI']}")
            except Exception as e:
                app.logger.error(f"Database creation failed: {str(e)}")
                raise

        app.logger.info("Authentication system initialized")
    else:
        app.logger.warning("Authentication system not available - running without user accounts")

    # Add basic health check endpoint
    @app.route('/')
    def health_check():
        return jsonify({
            'status': 'healthy',
            'service': 'BoardMinutes API',
            'version': '1.0.0',
            'timestamp': datetime.now().isoformat()
        })

    # Add comprehensive health check if database optimizer is available
    if DATABASE_OPTIMIZER_AVAILABLE:
        @app.route('/api/health')
        def comprehensive_health_check():
            try:
                health_status = {
                    'status': 'healthy',
                    'service': 'MinuteMate API',
                    'version': '1.0.0',
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'checks': {}
                }

                # Database health check
                try:
                    db_health = get_database_health()
                    health_status['checks']['database'] = db_health
                except Exception as e:
                    health_status['checks']['database'] = {
                        'status': 'unhealthy',
                        'error': str(e)
                    }
                    health_status['status'] = 'degraded'

                return jsonify(health_status)

            except Exception as e:
                return jsonify({
                    'status': 'unhealthy',
                    'service': 'MinuteMate API',
                    'error': str(e),
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }), 500

    # Add API documentation endpoints if available
    if DOCS_AVAILABLE:
        try:
            add_documentation_endpoints(app)
            app.logger.info("API documentation endpoints added")
        except Exception as e:
            app.logger.warning(f"API documentation setup failed: {e}")

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
    logger.info("BoardMinutes application initialized successfully")

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

# Initialize AI processor
ai_processor = AIProcessor()
app.ai_processor = ai_processor

# Initialize document generator
document_generator = DocumentGenerator(app.config['OUTPUT_FOLDER'] + '/documents')
app.document_generator = document_generator

# Initialize mock processor (fallback)
mock_processor = get_mock_processor(job_tracker, file_storage)
app.mock_processor = mock_processor

def allowed_file(filename):
    """Check if uploaded file has an allowed extension"""
    if '.' not in filename:
        return False

    extension = filename.rsplit('.', 1)[1].lower()

    # Get allowed extensions from config
    config_obj = app.config
    allowed_audio = config_obj.get('ALLOWED_AUDIO_EXTENSIONS', set())
    allowed_video = config_obj.get('ALLOWED_VIDEO_EXTENSIONS', set())
    allowed_transcript = {'txt', 'pdf', 'docx', 'doc', 'rtf'}  # Transcript file extensions
    allowed_extensions = allowed_audio | allowed_video | allowed_transcript

    return extension in allowed_extensions

def allowed_transcript_file(filename):
    """Check if uploaded transcript file has an allowed extension"""
    if '.' not in filename:
        return False

    extension = filename.rsplit('.', 1)[1].lower()
    allowed_transcript_extensions = {'txt', 'pdf', 'docx', 'doc'}

    return extension in allowed_transcript_extensions

def process_transcript_text(transcript_text, job_id, form_data):
    """Process text transcript directly"""
    logger = logging.getLogger(__name__)

    try:
        # Get processing options
        language = form_data.get('language', 'auto')
        format_type = form_data.get('format', 'formal')

        # Create job entry
        job_tracker.create_job(
            job_id=job_id,
            filename='transcript.txt',
            file_size=f"{len(transcript_text.encode('utf-8'))} bytes",
            source_type='transcript_text'
        )

        # Create Meeting record in database immediately
        from models import Meeting, db
        from datetime import datetime, timezone

        # Use authenticated user (login_required decorator ensures current_user is authenticated)
        user_id = current_user.id

        meeting = Meeting(
            user_id=user_id,
            title='Processing Transcript...',
            description=f"Meeting being processed from transcript upload",
            meeting_date=datetime.now(timezone.utc),
            original_filename='transcript.txt',
            file_type='text/plain',
            job_id=job_id,
            status='processing',
            transcript=transcript_text
        )

        db.session.add(meeting)
        db.session.commit()
        meeting_id = meeting.id
        logger.info(f"Created Meeting record {meeting_id} for job {job_id}")

        # Start processing in background
        def process_transcript_background():
            try:
                # AI-powered processing
                job_tracker.update_job(job_id, status=JobStatus.PARSING, message='Analyzing transcript with AI...')

                # Try AI processing first
                if app.ai_processor.is_available():
                    logger.info(f"Processing transcript with AI for job {job_id}")
                    meeting_minutes = app.ai_processor.process_transcript(transcript_text, 'transcript.txt')
                else:
                    logger.info(f"AI not available, using enhanced mock processing for job {job_id}")
                    job_tracker.update_job(job_id, status=JobStatus.FORMATTING, message='Using enhanced processing...')
                    meeting_minutes = generate_meeting_minutes_from_transcript(transcript_text, language, format_type)

                job_tracker.update_job(job_id, status=JobStatus.EXPORTING, message='Generating professional documents...')

                # Store results using document generator
                results_path = store_meeting_minutes_results(job_id, meeting_minutes)

                # Update Meeting record in database
                with app.app_context():
                    from models import Meeting, db
                    from datetime import datetime, timezone

                    meeting = Meeting.query.get(meeting_id)
                    if meeting:
                        meeting_info = meeting_minutes.get('meeting_info', {})
                        meeting.title = meeting_info.get('title', 'Transcript Meeting')
                        meeting.status = 'completed'
                        meeting.attendees = meeting_minutes.get('attendees', [])
                        meeting.agenda_items = meeting_minutes.get('agenda_items', [])
                        meeting.motions = meeting_minutes.get('motions', [])
                        meeting.action_items = meeting_minutes.get('action_items', [])
                        meeting.key_decisions = meeting_minutes.get('key_decisions', [])

                        # Set file paths if available
                        if results_path and os.path.exists(results_path):
                            meeting.json_file_path = results_path
                            # Look for generated HTML and DOCX files
                            base_path = os.path.dirname(results_path)
                            base_name = os.path.splitext(os.path.basename(results_path))[0]

                            html_path = os.path.join(base_path, f"{base_name}.html")
                            if os.path.exists(html_path):
                                meeting.html_file_path = html_path

                            docx_path = os.path.join(base_path, f"{base_name}.docx")
                            if os.path.exists(docx_path):
                                meeting.docx_file_path = docx_path

                        db.session.commit()
                        logger.info(f"Updated Meeting record {meeting_id} for job {job_id}")

                job_tracker.update_job(job_id, status=JobStatus.COMPLETED, message='Meeting minutes generated successfully', result_file=results_path)

            except Exception as e:
                logger.error(f"Transcript processing failed for job {job_id}: {str(e)}")
                # Update meeting status to failed
                try:
                    with app.app_context():
                        from models import Meeting, db
                        meeting = Meeting.query.get(meeting_id)
                        if meeting:
                            meeting.status = 'failed'
                            db.session.commit()
                except:
                    pass
                job_tracker.update_job(job_id, status=JobStatus.FAILED, error=f'Processing failed: {str(e)}')

        # Start background processing
        import threading
        thread = threading.Thread(target=process_transcript_background)
        thread.daemon = True
        thread.start()

        return jsonify({
            'success': True,
            'job_id': job_id,
            'filename': 'transcript.txt',
            'file_size': f"{len(transcript_text.encode('utf-8'))} bytes",
            'message': 'Transcript processing started',
            'estimated_time': '1-2 minutes'
        }), 202

    except Exception as e:
        logger.error(f"Failed to start transcript processing: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Failed to process transcript: {str(e)}'
        }), 500

def process_transcript_file(file, job_id, form_data, storage_result):
    """Process uploaded transcript file"""
    logger = logging.getLogger(__name__)

    try:
        # Get processing options
        language = form_data.get('language', 'auto')
        format_type = form_data.get('format', 'formal')

        # File is already stored and job is already created, just use the storage result

        # Create Meeting record in database immediately
        from models import Meeting, db
        from datetime import datetime, timezone

        # Use authenticated user (login_required decorator ensures current_user is authenticated)
        user_id = current_user.id

        meeting = Meeting(
            user_id=user_id,
            title=f'Processing {file.filename}...',
            description=f"Meeting being processed from file upload: {file.filename}",
            meeting_date=datetime.now(timezone.utc),
            original_filename=file.filename,
            file_type=file.content_type,
            file_size=file.content_length,
            job_id=job_id,
            status='processing',
            transcript=None  # Will be set after file processing
        )

        db.session.add(meeting)
        db.session.commit()
        meeting_id = meeting.id
        logger.info(f"Created Meeting record {meeting_id} for job {job_id}")

        # Start processing in background
        def process_transcript_file_background():
            try:
                # Extract text from file
                job_tracker.update_job(job_id, status=JobStatus.TRANSCRIBING, message='Extracting text from file...')
                time.sleep(2)

                # Read file content based on type
                file_path = storage_result['file_path']
                transcript_text = extract_text_from_file(file_path, file.filename)

                job_tracker.update_job(job_id, status=JobStatus.PARSING, message='Analyzing transcript with AI...')

                # Try AI processing first
                if app.ai_processor.is_available():
                    logger.info(f"Processing transcript file with AI for job {job_id}")
                    meeting_minutes = app.ai_processor.process_transcript(transcript_text, file.filename)
                else:
                    logger.info(f"AI not available, using enhanced mock processing for job {job_id}")
                    job_tracker.update_job(job_id, status=JobStatus.FORMATTING, message='Using enhanced processing...')
                    meeting_minutes = generate_meeting_minutes_from_transcript(transcript_text, language, format_type)

                job_tracker.update_job(job_id, status=JobStatus.EXPORTING, message='Generating professional documents...')

                # Store results
                results_path = store_meeting_minutes_results(job_id, meeting_minutes)

                # Create Meeting record in database
                with app.app_context():
                    from models import Meeting, db, User
                    from datetime import datetime, timezone

                    meeting = Meeting.query.get(meeting_id)
                    if meeting:
                        meeting_info = meeting_minutes.get('meeting_info', {})
                        meeting.title = meeting_info.get('title', f"Meeting - {file.filename}")
                        meeting.status = 'completed'
                        meeting.transcript = transcript_text
                        meeting.file_size = len(transcript_text)
                        meeting.attendees = meeting_minutes.get('attendees', [])
                        meeting.agenda_items = meeting_minutes.get('agenda_items', [])
                        meeting.motions = meeting_minutes.get('motions', [])
                        meeting.action_items = meeting_minutes.get('action_items', [])
                        meeting.key_decisions = meeting_minutes.get('key_decisions', [])

                    # Set file paths if available
                    if results_path and os.path.exists(results_path):
                        meeting.json_file_path = results_path
                        # Look for generated HTML and DOCX files
                        base_path = os.path.dirname(results_path)
                        base_name = os.path.splitext(os.path.basename(results_path))[0]

                        html_path = os.path.join(base_path, f"{base_name}.html")
                        if os.path.exists(html_path):
                            meeting.html_file_path = html_path

                        docx_path = os.path.join(base_path, f"{base_name}.docx")
                        if os.path.exists(docx_path):
                            meeting.docx_file_path = docx_path

                        db.session.commit()
                        logger.info(f"Updated Meeting record {meeting_id} for job {job_id}")

                job_tracker.update_job(job_id, status=JobStatus.COMPLETED, message='Meeting minutes generated successfully', result_file=results_path)

            except Exception as e:
                logger.error(f"Transcript file processing failed for job {job_id}: {str(e)}")
                # Update meeting status to failed
                try:
                    with app.app_context():
                        from models import Meeting, db
                        meeting = Meeting.query.get(meeting_id)
                        if meeting:
                            meeting.status = 'failed'
                            db.session.commit()
                except:
                    pass
                job_tracker.update_job(job_id, status=JobStatus.FAILED, error=f'Processing failed: {str(e)}')

        # Start background processing
        import threading
        thread = threading.Thread(target=process_transcript_file_background)
        thread.daemon = True
        thread.start()

        return jsonify({
            'success': True,
            'job_id': job_id,
            'filename': file.filename,
            'file_size': formatted_size,
            'message': 'Transcript file processing started',
            'estimated_time': '2-3 minutes'
        }), 202

    except Exception as e:
        logger.error(f"Failed to start transcript file processing: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Failed to process transcript file: {str(e)}'
        }), 500

@app.route('/')
def index():
    """Health check and API info endpoint"""
    return jsonify({
        'message': 'BoardMinutes API is running',
        'version': '1.0.0',
        'status': 'healthy',
        'endpoints': {
            'upload': '/api/upload',
            'upload_url': '/api/upload-url',
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

# Frontend serving routes
@app.route('/frontend')
@app.route('/frontend/')
def serve_frontend():
    """Serve the main frontend page"""
    # Try different path resolutions for Railway compatibility
    import os
    frontend_paths = [
        '../frontend',
        'frontend',
        '/app/frontend',
        os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend')
    ]

    for frontend_path in frontend_paths:
        try:
            if os.path.exists(os.path.join(frontend_path, 'index.html')):
                return send_from_directory(frontend_path, 'index.html')
        except:
            continue

    # Fallback: return a simple HTML page with error info
    return '''
    <html>
    <head><title>MinuteMate Frontend</title></head>
    <body>
        <h1>MinuteMate Frontend Loading Issue</h1>
        <p>Frontend files not found. Checking paths...</p>
        <p>Current working directory: ''' + os.getcwd() + '''</p>
        <p>Available paths: ''' + str([p for p in frontend_paths if os.path.exists(p)]) + '''</p>
    </body>
    </html>
    '''

@app.route('/frontend/<path:filename>')
def serve_frontend_files(filename):
    """Serve frontend static files"""
    import os
    frontend_paths = [
        '../frontend',
        'frontend',
        '/app/frontend',
        os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend')
    ]

    for frontend_path in frontend_paths:
        try:
            if os.path.exists(os.path.join(frontend_path, filename)):
                return send_from_directory(frontend_path, filename)
        except:
            continue

    return "File not found", 404

@app.route('/shared/<token>')
def view_shared_meeting(token):
    """View a shared meeting"""
    import os
    frontend_paths = [
        '../frontend',
        'frontend',
        '/app/frontend',
        os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend')
    ]

    for frontend_path in frontend_paths:
        try:
            if os.path.exists(os.path.join(frontend_path, 'shared.html')):
                return send_from_directory(frontend_path, 'shared.html')
        except:
            continue

    # If file not found, return a simple HTML page
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Shared Meeting - MinuteMate</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            .container {{ max-width: 800px; margin: 0 auto; }}
            .error {{ color: #dc3545; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>MinuteMate - Shared Meeting</h1>
            <p class="error">Shared meeting view is being set up. Token: {token}</p>
            <p>This feature will be available soon.</p>
        </div>
    </body>
    </html>
    '''

@app.route('/api/upload', methods=['POST'])
@login_required
def upload_file():
    """Handle file upload for audio/video/transcript processing with enhanced validation"""
    logger = logging.getLogger(__name__)

    try:
        # Check upload type
        upload_type = request.form.get('upload_type', 'file')

        if upload_type == 'transcript_text':
            # Handle text transcript
            transcript_text = request.form.get('transcript_text')
            if not transcript_text or not transcript_text.strip():
                raise ValidationError('No transcript text provided', field='transcript_text')

            # Generate job ID for tracking
            job_id = generate_job_id('transcript.txt')

            # Process transcript directly
            return process_transcript_text(transcript_text, job_id, request.form)

        elif upload_type == 'transcript_file':
            # Handle transcript file upload
            if 'transcript_file' not in request.files:
                raise ValidationError('No transcript file provided', field='transcript_file')

            file = request.files['transcript_file']
            if file.filename == '':
                raise ValidationError('No transcript file selected', field='transcript_file')

            # Check if it's a valid transcript file type
            if not allowed_transcript_file(file.filename):
                raise ValidationError(
                    'Invalid transcript file type. Supported: TXT, PDF, DOCX',
                    field='transcript_file',
                    value=file.filename
                )

            # Generate job ID for tracking
            job_id = generate_job_id(file.filename)

            # Process transcript file
            return process_transcript_file(file, job_id, request.form)

        else:
            # Handle regular audio/video file upload
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

        # Start processing the job automatically
        file_type = storage_result.get('file_info', {}).get('file_type', 'unknown')
        if file_type == 'transcript':
            # Process transcript file with AI
            process_transcript_file(file, job_id, request.form, storage_result)
        else:
            # Process audio/video file with mock processor (for now)
            app.mock_processor.start_processing(job_id)

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

@app.route('/api/upload-url', methods=['POST'])
@login_required
def upload_from_url():
    """Handle file upload from URL (e.g., Zoom recordings, Google Drive, etc.)"""
    logger = logging.getLogger(__name__)

    try:
        # Get JSON data
        if not request.is_json:
            raise ValidationError('Request must be JSON', field='content-type')

        data = request.get_json()
        if not data:
            raise ValidationError('No JSON data provided')

        # Validate required fields
        url = data.get('url', '').strip()
        if not url:
            raise ValidationError('URL is required', field='url')

        # Validate URL format
        try:
            parsed_url = urlparse(url)
            if not parsed_url.scheme or not parsed_url.netloc:
                raise ValidationError('Invalid URL format', field='url', value=url)
        except Exception:
            raise ValidationError('Invalid URL format', field='url', value=url)

        # Optional parameters
        filename = data.get('filename', '').strip()
        language = data.get('language', 'auto')
        output_format = data.get('format', 'roberts_rules')

        logger.info(f"Starting URL download from: {url}")

        # Download file from URL
        try:
            # Set headers to mimic a browser request
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'audio/*,video/*,*/*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }

            # Make request with timeout
            response = requests.get(url, headers=headers, timeout=30, stream=True)
            response.raise_for_status()

            # Check content type
            content_type = response.headers.get('content-type', '').lower()
            logger.info(f"Downloaded content type: {content_type}")

            # Check if this is a streaming platform URL that needs special handling
            domain = parsed_url.netloc.lower()
            is_streaming_platform = any(platform in domain for platform in [
                'youtube.com', 'youtu.be', 'vimeo.com', 'twitch.tv',
                'facebook.com', 'instagram.com', 'tiktok.com'
            ])

            if is_streaming_platform:
                raise FileProcessingError(
                    f'Streaming platform URLs are not supported yet. Please download the file first and upload it directly, or use a direct link to the audio/video file.',
                    operation='url_validation'
                )

            # Validate content type for direct file URLs
            allowed_content_types = [
                'audio/', 'video/', 'application/octet-stream'
            ]

            if not any(content_type.startswith(ct) for ct in allowed_content_types):
                # Try to determine from URL extension if content-type is not helpful
                url_path = Path(parsed_url.path)
                if not url_path.suffix.lower() in ['.mp3', '.wav', '.mp4', '.avi', '.mov', '.flac', '.m4a', '.aac', '.ogg', '.mkv', '.wmv']:
                    raise FileProcessingError(
                        f'This appears to be a web page (content-type: {content_type}) rather than a direct link to an audio/video file. Please use a direct download link.',
                        operation='url_validation'
                    )

            # Determine filename
            if not filename:
                # Try to get filename from URL or Content-Disposition header
                content_disposition = response.headers.get('content-disposition', '')
                if 'filename=' in content_disposition:
                    filename = content_disposition.split('filename=')[1].strip('"\'')
                else:
                    # Extract from URL path
                    url_filename = Path(parsed_url.path).name
                    if url_filename and '.' in url_filename:
                        filename = url_filename
                    else:
                        # Generate a filename based on URL
                        domain = parsed_url.netloc.replace('www.', '')
                        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                        filename = f"{domain}_{timestamp}.mp4"  # Default to mp4

            # Ensure filename is secure
            filename = secure_filename(filename)
            if not filename:
                filename = f"download_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"

            # Check file size from headers
            content_length = response.headers.get('content-length')
            if content_length:
                file_size = int(content_length)
                max_size = app.config.get('MAX_CONTENT_LENGTH', 500 * 1024 * 1024)
                if file_size > max_size:
                    raise FileProcessingError(
                        f'File too large: {file_size} bytes (max: {max_size} bytes)',
                        operation='url_download'
                    )

            # Create temporary file to download content
            temp_dir = app.config.get('TEMP_FOLDER', 'temp')
            os.makedirs(temp_dir, exist_ok=True)

            temp_file_path = os.path.join(temp_dir, f"download_{generate_job_id(filename)}")

            # Download file in chunks
            downloaded_size = 0
            max_size = app.config.get('MAX_CONTENT_LENGTH', 500 * 1024 * 1024)

            with open(temp_file_path, 'wb') as temp_file:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        temp_file.write(chunk)
                        downloaded_size += len(chunk)

                        # Check size limit during download
                        if downloaded_size > max_size:
                            temp_file.close()
                            os.unlink(temp_file_path)
                            raise FileProcessingError(
                                f'File too large: exceeded {max_size} bytes during download',
                                operation='url_download'
                            )

            logger.info(f"Downloaded {downloaded_size} bytes to {temp_file_path}")

            # Now process the downloaded file like a regular upload
            storage_result = file_storage_manager.store_file(
                temp_file_path,
                filename,
                validate_content=True
            )

            # Clean up temporary file
            try:
                os.unlink(temp_file_path)
            except:
                pass  # Ignore cleanup errors

            if not storage_result['success']:
                raise FileProcessingError(
                    storage_result['error'],
                    operation='file_storage'
                )

            # Generate job ID and create job entry
            job_id = generate_job_id(filename)

            # Create job entry
            job_tracker.create_job(
                job_id=job_id,
                filename=filename,
                file_path=storage_result['file_path'],
                file_size=format_file_size(downloaded_size),
                language=language,
                output_format=output_format,
                source_type='url',
                source_url=url
            )

            # Prepare response data
            response_data = {
                'job_id': job_id,
                'filename': filename,
                'file_size': format_file_size(downloaded_size),
                'language': language,
                'format': output_format,
                'source_type': 'url',
                'source_url': url,
                'status': 'uploaded',
                'message': 'File downloaded and uploaded successfully'
            }

            # Start processing the job automatically
            # Note: URL downloads are typically audio/video, so use mock processor for now
            app.mock_processor.start_processing(job_id)

            # Record successful request
            health_monitor.record_request(True, time.time() - g.start_time)

            response = create_response(True, 'File downloaded and uploaded successfully', response_data)
            return jsonify(response), 200

        except requests.exceptions.Timeout:
            raise FileProcessingError(
                'Download timeout: The file took too long to download',
                operation='url_download'
            )
        except requests.exceptions.ConnectionError:
            raise FileProcessingError(
                'Connection error: Unable to connect to the URL',
                operation='url_download'
            )
        except requests.exceptions.HTTPError as e:
            raise FileProcessingError(
                f'HTTP error: {e.response.status_code} - {e.response.reason}',
                operation='url_download'
            )
        except requests.exceptions.RequestException as e:
            raise FileProcessingError(
                f'Download failed: {str(e)}',
                operation='url_download'
            )

    except (ValidationError, FileProcessingError, SecurityError):
        # These are handled by the error handler
        health_monitor.record_request(False, time.time() - g.start_time)
        raise
    except Exception as e:
        health_monitor.record_request(False, time.time() - g.start_time, str(e))
        logger.error(f"Unexpected URL upload error: {str(e)}", exc_info=True)
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

@app.route('/api/preview/<job_id>', methods=['GET'])
def preview_result(job_id):
    """Preview meeting minutes in HTML format"""
    logger = logging.getLogger(__name__)

    job_info = job_tracker.get_job(job_id)
    logger.info(f"Preview request for job {job_id}: {job_info}")

    if not job_info:
        response = create_response(False, 'Job not found')
        return jsonify(response), 404

    if job_info['status'] != JobStatus.COMPLETED.value:
        response = create_response(
            False,
            f"Job not completed. Current status: {job_info['status']}"
        )
        return jsonify(response), 400

    result_file = job_info.get('result_file')
    if not result_file:
        response = create_response(False, 'No result file specified')
        return jsonify(response), 404

    # Look for HTML version of the file
    html_file = result_file.replace('.docx', '.html').replace('.json', '.html')
    if not html_file.endswith('.html'):
        html_file = result_file.rsplit('.', 1)[0] + '.html'

    # Check if HTML file exists in the same directory
    import glob
    output_dir = Path(app.config['OUTPUT_FOLDER']) / 'documents'
    html_files = glob.glob(str(output_dir / f"meeting_minutes_{job_id}_*.html"))

    if html_files:
        html_file = html_files[0]  # Use the most recent one
        try:
            return send_file(
                html_file,
                mimetype='text/html',
                as_attachment=False  # Display in browser, don't download
            )
        except Exception as e:
            logger.error(f"Preview error for job {job_id}: {str(e)}")
            response = create_response(False, 'Error loading preview')
            return jsonify(response), 500
    else:
        response = create_response(False, 'HTML preview not available')
        return jsonify(response), 404

@app.route('/api/download/<job_id>', methods=['GET'])
def download_result(job_id):
    """Download processed meeting minutes"""
    logger = logging.getLogger(__name__)

    job_info = job_tracker.get_job(job_id)
    logger.info(f"Download request for job {job_id}: {job_info}")

    if not job_info:
        response = create_response(False, 'Job not found')
        return jsonify(response), 404

    if job_info['status'] != JobStatus.COMPLETED.value:
        logger.warning(f"Job {job_id} not completed. Status: {job_info['status']}")
        response = create_response(
            False,
            f"Job not completed. Current status: {job_info['status']}"
        )
        return jsonify(response), 400

    result_file = job_info.get('result_file')
    logger.info(f"Result file for job {job_id}: {result_file}")

    if not result_file:
        response = create_response(False, 'No result file specified')
        return jsonify(response), 404

    if not os.path.exists(result_file):
        logger.error(f"Result file does not exist: {result_file}")
        response = create_response(False, 'Result file not found on disk')
        return jsonify(response), 404

    try:
        result_file = job_info['result_file']

        if not os.path.exists(result_file):
            response = create_response(False, 'Result file not found on disk')
            return jsonify(response), 404

        # Determine file type and download name
        if result_file.endswith('.html'):
            download_name = f"meeting_minutes_{job_id}.html"
            mimetype = 'text/html'
        elif result_file.endswith('.docx'):
            download_name = f"meeting_minutes_{job_id}.docx"
            mimetype = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        elif result_file.endswith('.pdf'):
            download_name = f"meeting_minutes_{job_id}.pdf"
            mimetype = 'application/pdf'
        elif result_file.endswith('.json'):
            download_name = f"meeting_minutes_{job_id}.json"
            mimetype = 'application/json'
        else:
            download_name = f"meeting_minutes_{job_id}.txt"
            mimetype = 'text/plain'

        return send_file(
            result_file,
            as_attachment=True,
            download_name=download_name,
            mimetype=mimetype
        )
    except Exception as e:
        app.logger.error(f"Download error for job {job_id}: {str(e)}")
        response = create_response(False, 'Error downloading file')
        return jsonify(response), 500

def extract_text_from_file(file_path, filename):
    """Extract text content from uploaded transcript files"""
    extension = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''

    if extension == 'txt':
        # Read plain text file
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()

    elif extension in ['pdf']:
        # For PDF files, we'll return a mock transcript for now
        # In a real implementation, you'd use PyPDF2 or similar
        return """
John Smith: Good morning everyone, let's start today's meeting.
Jane Doe: Thank you John. First item on the agenda is the budget review.
Bob Johnson: I'd like to make a motion to approve the quarterly budget.
Alice Williams: I second that motion.
John Smith: All in favor? [Multiple voices: Aye] Motion carries.
Jane Doe: Next item is the project timeline discussion.
Bob Johnson: We need to extend the deadline by two weeks.
Alice Williams: I agree, the current timeline is too aggressive.
John Smith: Any objections? [Silence] Motion to extend deadline by two weeks.
Jane Doe: I second that.
John Smith: All in favor? [Multiple voices: Aye] Motion carries.
        """.strip()

    elif extension in ['docx', 'doc']:
        # For Word documents, we'll return a mock transcript for now
        # In a real implementation, you'd use python-docx
        return """
Meeting Transcript - Board Meeting
Date: Today
Attendees: John Smith (Chair), Jane Doe (Secretary), Bob Johnson (Treasurer), Alice Williams (Member)

John Smith: Good morning everyone, let's start today's meeting.
Jane Doe: Thank you John. First item on the agenda is the budget review.
Bob Johnson: I'd like to make a motion to approve the quarterly budget of $50,000.
Alice Williams: I second that motion.
John Smith: All in favor? [Multiple voices: Aye] Motion carries.
Jane Doe: Next item is the project timeline discussion.
Bob Johnson: We need to extend the deadline by two weeks due to resource constraints.
Alice Williams: I agree, the current timeline is too aggressive given our current workload.
John Smith: Any objections? [Silence] I'll make a motion to extend the project deadline by two weeks.
Jane Doe: I second that motion.
John Smith: All in favor? [Multiple voices: Aye] Motion carries.
Alice Williams: Should we schedule a follow-up meeting to review progress?
Bob Johnson: Yes, I suggest we meet again in two weeks.
John Smith: Agreed. Meeting adjourned.
        """.strip()

    else:
        raise ValueError(f"Unsupported file type: {extension}")

def store_meeting_minutes_results(job_id, meeting_minutes):
    """Store meeting minutes results in multiple user-friendly formats"""

    # Generate documents in multiple formats
    document_paths = app.document_generator.generate_documents(meeting_minutes, job_id)

    # Return the primary document path (prefer PDF for sharing, then DOCX for editing, then HTML, then JSON)
    if 'pdf' in document_paths:
        return document_paths['pdf']
    elif 'docx' in document_paths:
        return document_paths['docx']
    elif 'html' in document_paths:
        return document_paths['html']
    else:
        return document_paths.get('json', '')

def generate_meeting_minutes_from_transcript(transcript_text, language='auto', format_type='formal'):
    """Generate structured meeting minutes from transcript text"""

    # Extract basic information from transcript
    lines = [line.strip() for line in transcript_text.split('\n') if line.strip()]

    # Simple speaker detection
    speakers = set()
    for line in lines:
        if ':' in line:
            speaker = line.split(':')[0].strip()
            if len(speaker.split()) <= 3:  # Likely a name
                speakers.add(speaker)

    # Count potential motions
    motion_keywords = ['motion', 'move', 'propose', 'second']
    motion_count = sum(1 for line in lines if any(keyword in line.lower() for keyword in motion_keywords))

    # Generate structured meeting minutes
    meeting_minutes = {
        "meeting_info": {
            "title": "Meeting Minutes",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "time": datetime.now().strftime("%H:%M"),
            "location": "Conference Room / Virtual",
            "meeting_type": "Regular Meeting"
        },
        "attendees": [
            {
                "name": speaker,
                "role": "Member" if i > 0 else "Chairperson",
                "present": True
            }
            for i, speaker in enumerate(sorted(speakers)[:8])  # Limit to 8 attendees
        ],
        "agenda_items": [
            {
                "item_number": 1,
                "title": "Budget Review",
                "discussion": "Discussion regarding quarterly budget allocation and approval.",
                "outcome": "Motion approved"
            },
            {
                "item_number": 2,
                "title": "Project Timeline",
                "discussion": "Review of current project timeline and resource allocation.",
                "outcome": "Timeline extended by two weeks"
            },
            {
                "item_number": 3,
                "title": "Next Steps",
                "discussion": "Planning for follow-up meetings and action items.",
                "outcome": "Follow-up meeting scheduled"
            }
        ],
        "motions": [
            {
                "motion_number": i + 1,
                "description": f"Motion {i + 1} extracted from transcript",
                "moved_by": list(speakers)[0] if speakers else "Unknown",
                "seconded_by": list(speakers)[1] if len(speakers) > 1 else "Unknown",
                "result": "Carried",
                "vote_count": {
                    "in_favor": len(speakers),
                    "against": 0,
                    "abstained": 0
                }
            }
            for i in range(min(motion_count, 3))  # Limit to 3 motions
        ],
        "action_items": [
            {
                "item_number": 1,
                "description": "Follow up on budget implementation",
                "assigned_to": list(speakers)[0] if speakers else "Unknown",
                "due_date": (datetime.now().replace(day=datetime.now().day + 7)).strftime("%Y-%m-%d"),
                "status": "Pending"
            },
            {
                "item_number": 2,
                "description": "Schedule follow-up meeting",
                "assigned_to": list(speakers)[1] if len(speakers) > 1 else "Unknown",
                "due_date": (datetime.now().replace(day=datetime.now().day + 14)).strftime("%Y-%m-%d"),
                "status": "Pending"
            }
        ],
        "next_meeting": {
            "date": (datetime.now().replace(day=datetime.now().day + 14)).strftime("%Y-%m-%d"),
            "time": "10:00 AM",
            "location": "Conference Room / Virtual"
        },
        "meeting_end_time": datetime.now().strftime("%H:%M"),
        "secretary": list(speakers)[1] if len(speakers) > 1 else "Unknown",
        "chairperson": list(speakers)[0] if speakers else "Unknown"
    }

    return meeting_minutes

# Add health check and monitoring endpoints
def add_monitoring_endpoints(app):
    """Add monitoring and health check endpoints"""

    @app.route('/')
    def health_check():
        return jsonify({
            'status': 'healthy',
            'service': 'MinuteMate API',
            'version': '1.0.0',
            'timestamp': datetime.now().isoformat()
        })

    @app.route('/api/health')
    def comprehensive_health_check():
        try:
            health_status = {
                'status': 'healthy',
                'service': 'MinuteMate API',
                'version': '1.0.0',
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'checks': {}
            }

            # Database health check
            try:
                db_health = get_database_health()
                health_status['checks']['database'] = db_health
            except Exception as e:
                health_status['checks']['database'] = {
                    'status': 'unhealthy',
                    'error': str(e)
                }
                health_status['status'] = 'degraded'

            # Redis health check (if available)
            try:
                redis_client = create_redis_client()
                if redis_client:
                    redis_client.ping()
                    health_status['checks']['redis'] = {'status': 'healthy'}
                else:
                    health_status['checks']['redis'] = {'status': 'not_configured'}
            except Exception as e:
                health_status['checks']['redis'] = {
                    'status': 'unhealthy',
                    'error': str(e)
                }
                health_status['status'] = 'degraded'

            # File system health check
            try:
                import os
                upload_dir = app.config.get('UPLOAD_FOLDER', '../uploads')
                output_dir = app.config.get('OUTPUT_FOLDER', '../output')

                fs_status = {
                    'upload_dir_writable': os.access(upload_dir, os.W_OK) if os.path.exists(upload_dir) else False,
                    'output_dir_writable': os.access(output_dir, os.W_OK) if os.path.exists(output_dir) else False
                }

                if fs_status['upload_dir_writable'] and fs_status['output_dir_writable']:
                    health_status['checks']['filesystem'] = {
                        'status': 'healthy',
                        **fs_status
                    }
                else:
                    health_status['checks']['filesystem'] = {
                        'status': 'unhealthy',
                        **fs_status
                    }
                    health_status['status'] = 'degraded'

            except Exception as e:
                health_status['checks']['filesystem'] = {
                    'status': 'unhealthy',
                    'error': str(e)
                }
                health_status['status'] = 'degraded'

            # AI service health check
            try:
                openai_key = app.config.get('OPENAI_API_KEY')
                if openai_key and openai_key != 'your-openai-api-key-here':
                    health_status['checks']['ai_service'] = {'status': 'configured'}
                else:
                    health_status['checks']['ai_service'] = {'status': 'not_configured'}
            except Exception as e:
                health_status['checks']['ai_service'] = {
                    'status': 'error',
                    'error': str(e)
                }

            return jsonify(health_status)

        except Exception as e:
            return jsonify({
                'status': 'unhealthy',
                'service': 'MinuteMate API',
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }), 500

    @app.route('/api/admin/reset-rate-limits', methods=['POST'])
    def reset_rate_limits():
        """Reset rate limits for debugging"""
        try:
            # Clear rate limits from security middleware
            if hasattr(app, 'security_middleware') and hasattr(app.security_middleware, 'rate_limiter'):
                app.security_middleware.rate_limiter.memory_store.clear()

            return jsonify({
                'success': True,
                'message': 'Rate limits reset successfully'
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/admin/system-info')
    def system_info():
        """Get system information and metrics"""
        try:
            import psutil
            import platform

            # System information
            system_info = {
                'platform': platform.platform(),
                'python_version': platform.python_version(),
                'cpu_count': psutil.cpu_count(),
                'memory_total': psutil.virtual_memory().total,
                'memory_available': psutil.virtual_memory().available,
                'memory_percent': psutil.virtual_memory().percent,
                'disk_usage': {
                    'total': psutil.disk_usage('/').total,
                    'used': psutil.disk_usage('/').used,
                    'free': psutil.disk_usage('/').free,
                    'percent': psutil.disk_usage('/').percent
                }
            }

            return jsonify({
                'success': True,
                'data': system_info
            })

        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

# Error handlers are now managed by the ErrorHandler class

if __name__ == '__main__':
    # Development server
    app.run(debug=True, host='0.0.0.0', port=5000)