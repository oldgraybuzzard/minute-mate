"""
MinuteMate Configuration
Centralized configuration management for the MinuteMate application.
"""

import os
from pathlib import Path

class BaseConfig:
    """Base configuration class"""
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # File upload settings
    MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 500MB max file size
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '..', 'uploads')
    OUTPUT_FOLDER = os.path.join(os.path.dirname(__file__), '..', 'output')
    TEMP_FOLDER = os.path.join(os.path.dirname(__file__), '..', 'temp')

    # File validation settings
    ENABLE_MIME_VALIDATION = True
    ENABLE_MALICIOUS_SCAN = True
    MAX_FILENAME_LENGTH = 255

    # File cleanup settings
    AUTO_CLEANUP_ENABLED = True
    CLEANUP_INTERVAL_HOURS = 6
    MAX_FILE_AGE_HOURS = 24
    TEMP_FILE_AGE_HOURS = 2

    # Allowed file extensions
    ALLOWED_AUDIO_EXTENSIONS = {
        'mp3', 'wav', 'flac', 'm4a', 'aac', 'ogg', 'wma'
    }
    ALLOWED_VIDEO_EXTENSIONS = {
        'mp4', 'avi', 'mov', 'mkv', 'wmv', 'flv', 'webm', '3gp'
    }

    # Storage organization
    ORGANIZE_BY_TYPE = True  # Separate audio and video files
    ORGANIZE_BY_DATE = False  # Create date-based subdirectories
    
    @property
    def ALLOWED_EXTENSIONS(self):
        return self.ALLOWED_AUDIO_EXTENSIONS | self.ALLOWED_VIDEO_EXTENSIONS
    
    # Whisper settings
    WHISPER_MODEL = os.environ.get('WHISPER_MODEL', 'base')  # tiny, base, small, medium, large
    WHISPER_LANGUAGE = os.environ.get('WHISPER_LANGUAGE', 'en')
    
    # Processing settings
    MAX_PROCESSING_TIME = 3600  # 1 hour max processing time
    CLEANUP_TEMP_FILES = True
    
    # Logging configuration
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_DIR = os.path.join(os.path.dirname(__file__), '..', 'logs')
    LOG_FILE = os.path.join(LOG_DIR, 'minutemate.log')
    LOG_MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT = 5
    LOG_ENABLE_CONSOLE = True
    LOG_ENABLE_FILE = True

    # Error handling settings
    ERROR_INCLUDE_TRACEBACK = False  # Set to True in development
    ERROR_SEND_EMAIL = False  # Email notifications for critical errors
    ERROR_EMAIL_RECIPIENTS = []

    # Security settings
    SECURITY_RATE_LIMIT_ENABLED = True
    SECURITY_RATE_LIMIT_REQUESTS = 100  # requests per hour
    SECURITY_RATE_LIMIT_WINDOW = 3600  # 1 hour in seconds
    SECURITY_MONITOR_ENABLED = True
    SECURITY_BLOCK_THRESHOLD = 10  # failed attempts before blocking

class DevelopmentConfig(BaseConfig):
    """Development configuration"""
    DEBUG = True
    TESTING = False
    ERROR_INCLUDE_TRACEBACK = True
    LOG_LEVEL = 'DEBUG'

class ProductionConfig(BaseConfig):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    # Override with more secure settings for production
    SECRET_KEY = os.environ.get('SECRET_KEY')
    if not SECRET_KEY:
        raise ValueError("SECRET_KEY environment variable must be set in production")

class TestingConfig(BaseConfig):
    """Testing configuration"""
    DEBUG = True
    TESTING = True
    # Use smaller limits for testing
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB for testing

# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config():
    """Get configuration based on environment"""
    env = os.environ.get('FLASK_ENV', 'default')
    return config.get(env, config['default'])
