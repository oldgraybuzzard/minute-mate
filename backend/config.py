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
    
    # Allowed file extensions
    ALLOWED_AUDIO_EXTENSIONS = {
        'mp3', 'wav', 'flac', 'm4a', 'aac', 'ogg', 'wma'
    }
    ALLOWED_VIDEO_EXTENSIONS = {
        'mp4', 'avi', 'mov', 'mkv', 'wmv', 'flv', 'webm'
    }
    
    @property
    def ALLOWED_EXTENSIONS(self):
        return self.ALLOWED_AUDIO_EXTENSIONS | self.ALLOWED_VIDEO_EXTENSIONS
    
    # Whisper settings
    WHISPER_MODEL = os.environ.get('WHISPER_MODEL', 'base')  # tiny, base, small, medium, large
    WHISPER_LANGUAGE = os.environ.get('WHISPER_LANGUAGE', 'en')
    
    # Processing settings
    MAX_PROCESSING_TIME = 3600  # 1 hour max processing time
    CLEANUP_TEMP_FILES = True
    
    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = os.path.join(os.path.dirname(__file__), '..', 'logs', 'minutemate.log')

class DevelopmentConfig(BaseConfig):
    """Development configuration"""
    DEBUG = True
    TESTING = False

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
