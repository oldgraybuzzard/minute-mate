"""
MinuteMate Utilities
Common utility functions for the MinuteMate application.
"""

import os
import hashlib
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import magic

logger = logging.getLogger(__name__)

def generate_job_id(filename: str) -> str:
    """Generate a unique job ID based on timestamp and filename"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    file_hash = hashlib.md5(filename.encode()).hexdigest()[:8]
    return f"job_{timestamp}_{file_hash}"

def validate_file_type(file_path: str, allowed_mimes: set) -> bool:
    """
    Validate file type using python-magic for security
    
    Args:
        file_path: Path to the file to validate
        allowed_mimes: Set of allowed MIME types
        
    Returns:
        bool: True if file type is valid, False otherwise
    """
    try:
        mime = magic.Magic(mime=True)
        file_mime = mime.from_file(file_path)
        logger.info(f"Detected MIME type: {file_mime} for file: {file_path}")
        return file_mime in allowed_mimes
    except Exception as e:
        logger.error(f"File validation error for {file_path}: {str(e)}")
        return False

def get_file_size(file_path: str) -> int:
    """Get file size in bytes"""
    try:
        return os.path.getsize(file_path)
    except OSError:
        return 0

def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f}{size_names[i]}"

def ensure_directory_exists(directory_path: str) -> None:
    """Ensure a directory exists, create if it doesn't"""
    Path(directory_path).mkdir(parents=True, exist_ok=True)

def cleanup_file(file_path: str) -> bool:
    """
    Safely remove a file
    
    Args:
        file_path: Path to the file to remove
        
    Returns:
        bool: True if file was removed successfully, False otherwise
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Cleaned up file: {file_path}")
            return True
        return False
    except Exception as e:
        logger.error(f"Error cleaning up file {file_path}: {str(e)}")
        return False

def get_audio_video_mimes() -> Dict[str, set]:
    """Get allowed MIME types for audio and video files"""
    return {
        'audio': {
            'audio/mpeg', 'audio/wav', 'audio/x-wav', 'audio/flac',
            'audio/mp4', 'audio/aac', 'audio/ogg', 'audio/x-ms-wma',
            'audio/x-m4a'
        },
        'video': {
            'video/mp4', 'video/x-msvideo', 'video/quicktime',
            'video/x-matroska', 'video/x-ms-wmv', 'video/x-flv',
            'video/webm', 'video/avi'
        }
    }

def is_audio_file(file_path: str) -> bool:
    """Check if file is an audio file"""
    mimes = get_audio_video_mimes()
    return validate_file_type(file_path, mimes['audio'])

def is_video_file(file_path: str) -> bool:
    """Check if file is a video file"""
    mimes = get_audio_video_mimes()
    return validate_file_type(file_path, mimes['video'])

def create_response(success: bool, message: str, data: Optional[Dict[Any, Any]] = None, 
                   status_code: int = 200) -> Dict[str, Any]:
    """
    Create a standardized API response
    
    Args:
        success: Whether the operation was successful
        message: Response message
        data: Optional data to include in response
        status_code: HTTP status code
        
    Returns:
        dict: Standardized response dictionary
    """
    response = {
        'success': success,
        'message': message,
        'timestamp': datetime.now().isoformat()
    }
    
    if data:
        response['data'] = data
        
    return response
