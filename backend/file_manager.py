"""
MinuteMate File Manager
Enhanced file validation, storage, and management system.
"""

import os
import hashlib
import logging
import tempfile
import shutil
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from pathlib import Path
import magic
from werkzeug.utils import secure_filename

logger = logging.getLogger(__name__)

class FileValidationError(Exception):
    """Custom exception for file validation errors"""
    pass

class FileStorageError(Exception):
    """Custom exception for file storage errors"""
    pass

class FileValidator:
    """Advanced file validation with security checks"""
    
    def __init__(self):
        self.allowed_mimes = {
            'audio': {
                'audio/mpeg', 'audio/wav', 'audio/x-wav', 'audio/flac',
                'audio/mp4', 'audio/aac', 'audio/ogg', 'audio/x-ms-wma',
                'audio/x-m4a', 'audio/webm'
            },
            'video': {
                'video/mp4', 'video/x-msvideo', 'video/quicktime',
                'video/x-matroska', 'video/x-ms-wmv', 'video/x-flv',
                'video/webm', 'video/avi', 'video/3gpp'
            }
        }
        
        self.allowed_extensions = {
            'audio': {'.mp3', '.wav', '.flac', '.m4a', '.aac', '.ogg', '.wma'},
            'video': {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.3gp'}
        }
        
        # Security patterns to detect potentially malicious files
        self.dangerous_patterns = [
            b'<script',
            b'javascript:',
            b'vbscript:',
            b'<?php',
            b'<%',
            b'#!/bin/',
            b'#!/usr/bin/'
        ]
        
        logger.info("FileValidator initialized")
    
    def validate_filename(self, filename: str) -> Tuple[bool, str]:
        """
        Validate filename for security and format
        
        Args:
            filename: Original filename
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not filename:
            return False, "Filename is empty"
        
        # Check for dangerous characters
        dangerous_chars = ['..', '/', '\\', ':', '*', '?', '"', '<', '>', '|']
        for char in dangerous_chars:
            if char in filename:
                return False, f"Filename contains dangerous character: {char}"
        
        # Check filename length
        if len(filename) > 255:
            return False, "Filename too long (max 255 characters)"
        
        # Check for valid extension
        file_ext = Path(filename).suffix.lower()
        all_extensions = self.allowed_extensions['audio'] | self.allowed_extensions['video']
        
        if file_ext not in all_extensions:
            return False, f"Unsupported file extension: {file_ext}"
        
        return True, ""
    
    def validate_file_size(self, file_path: str, max_size_bytes: int) -> Tuple[bool, str]:
        """
        Validate file size
        
        Args:
            file_path: Path to file
            max_size_bytes: Maximum allowed size in bytes
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            file_size = os.path.getsize(file_path)
            if file_size > max_size_bytes:
                max_mb = max_size_bytes / (1024 * 1024)
                actual_mb = file_size / (1024 * 1024)
                return False, f"File too large: {actual_mb:.1f}MB (max: {max_mb:.1f}MB)"
            
            if file_size == 0:
                return False, "File is empty"
            
            return True, ""
        except OSError as e:
            return False, f"Cannot read file size: {str(e)}"
    
    def validate_mime_type(self, file_path: str) -> Tuple[bool, str, str]:
        """
        Validate MIME type using python-magic
        
        Args:
            file_path: Path to file
            
        Returns:
            Tuple of (is_valid, error_message, detected_mime)
        """
        try:
            mime = magic.Magic(mime=True)
            detected_mime = mime.from_file(file_path)
            
            all_allowed_mimes = self.allowed_mimes['audio'] | self.allowed_mimes['video']
            
            if detected_mime not in all_allowed_mimes:
                return False, f"Invalid file type detected: {detected_mime}", detected_mime
            
            return True, "", detected_mime
        except Exception as e:
            return False, f"MIME type detection failed: {str(e)}", ""
    
    def scan_for_malicious_content(self, file_path: str, scan_bytes: int = 8192) -> Tuple[bool, str]:
        """
        Scan file for potentially malicious content
        
        Args:
            file_path: Path to file
            scan_bytes: Number of bytes to scan from beginning
            
        Returns:
            Tuple of (is_safe, warning_message)
        """
        try:
            with open(file_path, 'rb') as f:
                content = f.read(scan_bytes)
            
            for pattern in self.dangerous_patterns:
                if pattern in content:
                    return False, f"Potentially malicious content detected: {pattern.decode('utf-8', errors='ignore')}"
            
            return True, ""
        except Exception as e:
            logger.warning(f"Malicious content scan failed for {file_path}: {e}")
            return True, "Could not scan for malicious content"
    
    def validate_file(self, file_path: str, original_filename: str, 
                     max_size_bytes: int) -> Dict[str, Any]:
        """
        Comprehensive file validation
        
        Args:
            file_path: Path to uploaded file
            original_filename: Original filename
            max_size_bytes: Maximum allowed file size
            
        Returns:
            Dictionary with validation results
        """
        results = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'file_info': {
                'size_bytes': 0,
                'mime_type': '',
                'file_type': '',
                'extension': ''
            }
        }
        
        # Validate filename
        filename_valid, filename_error = self.validate_filename(original_filename)
        if not filename_valid:
            results['valid'] = False
            results['errors'].append(f"Filename validation failed: {filename_error}")
        
        # Validate file size
        size_valid, size_error = self.validate_file_size(file_path, max_size_bytes)
        if not size_valid:
            results['valid'] = False
            results['errors'].append(f"File size validation failed: {size_error}")
        else:
            results['file_info']['size_bytes'] = os.path.getsize(file_path)
        
        # Validate MIME type
        mime_valid, mime_error, detected_mime = self.validate_mime_type(file_path)
        if not mime_valid:
            results['valid'] = False
            results['errors'].append(f"MIME type validation failed: {mime_error}")
        else:
            results['file_info']['mime_type'] = detected_mime
            # Determine file type
            if detected_mime in self.allowed_mimes['audio']:
                results['file_info']['file_type'] = 'audio'
            elif detected_mime in self.allowed_mimes['video']:
                results['file_info']['file_type'] = 'video'
        
        # Scan for malicious content
        safe, warning = self.scan_for_malicious_content(file_path)
        if not safe:
            results['valid'] = False
            results['errors'].append(f"Security scan failed: {warning}")
        elif warning:
            results['warnings'].append(warning)
        
        # Set file extension
        results['file_info']['extension'] = Path(original_filename).suffix.lower()
        
        return results

class FileStorageManager:
    """Manages file storage with organization and cleanup"""
    
    def __init__(self, base_upload_dir: str, base_output_dir: str, temp_dir: str):
        """
        Initialize file storage manager
        
        Args:
            base_upload_dir: Base directory for uploads
            base_output_dir: Base directory for outputs
            temp_dir: Temporary directory
        """
        self.base_upload_dir = Path(base_upload_dir)
        self.base_output_dir = Path(base_output_dir)
        self.temp_dir = Path(temp_dir)
        
        # Create directory structure
        self._ensure_directories()
        
        self.validator = FileValidator()
        logger.info(f"FileStorageManager initialized with upload_dir: {base_upload_dir}")
    
    def _ensure_directories(self) -> None:
        """Ensure all required directories exist"""
        directories = [
            self.base_upload_dir,
            self.base_upload_dir / 'audio',
            self.base_upload_dir / 'video',
            self.base_output_dir,
            self.base_output_dir / 'documents',
            self.base_output_dir / 'transcripts',
            self.temp_dir
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Ensured directory exists: {directory}")
    
    def _generate_secure_filename(self, original_filename: str, job_id: str) -> str:
        """
        Generate a secure filename with job ID
        
        Args:
            original_filename: Original filename
            job_id: Job identifier
            
        Returns:
            Secure filename
        """
        # Get file extension
        file_ext = Path(original_filename).suffix.lower()
        
        # Create secure base name
        secure_name = secure_filename(Path(original_filename).stem)
        
        # Combine with job ID for uniqueness
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        secure_filename_final = f"{job_id}_{timestamp}_{secure_name}{file_ext}"
        
        return secure_filename_final
    
    def _get_storage_path(self, filename: str, file_type: str) -> Path:
        """
        Get the storage path for a file based on its type
        
        Args:
            filename: Filename
            file_type: Type of file (audio/video)
            
        Returns:
            Full storage path
        """
        if file_type == 'audio':
            return self.base_upload_dir / 'audio' / filename
        elif file_type == 'video':
            return self.base_upload_dir / 'video' / filename
        else:
            return self.base_upload_dir / filename
    
    def store_uploaded_file(self, uploaded_file, original_filename: str, 
                          job_id: str, max_size_bytes: int) -> Dict[str, Any]:
        """
        Store uploaded file with validation and organization
        
        Args:
            uploaded_file: Flask uploaded file object
            original_filename: Original filename
            job_id: Job identifier
            max_size_bytes: Maximum allowed file size
            
        Returns:
            Dictionary with storage results
        """
        temp_path = None
        final_path = None
        
        try:
            # Create temporary file
            temp_fd, temp_path = tempfile.mkstemp(
                suffix=Path(original_filename).suffix,
                dir=self.temp_dir
            )
            os.close(temp_fd)
            
            # Save uploaded file to temporary location
            uploaded_file.save(temp_path)
            
            # Validate the file
            validation_results = self.validator.validate_file(
                temp_path, original_filename, max_size_bytes
            )
            
            if not validation_results['valid']:
                raise FileValidationError(f"File validation failed: {validation_results['errors']}")
            
            # Generate secure filename
            secure_filename = self._generate_secure_filename(original_filename, job_id)
            
            # Determine storage path
            file_type = validation_results['file_info']['file_type']
            final_path = self._get_storage_path(secure_filename, file_type)
            
            # Move file to final location
            shutil.move(temp_path, final_path)
            temp_path = None  # File moved successfully
            
            # Set appropriate permissions
            os.chmod(final_path, 0o644)
            
            storage_info = {
                'success': True,
                'file_path': str(final_path),
                'secure_filename': secure_filename,
                'file_type': file_type,
                'file_info': validation_results['file_info'],
                'warnings': validation_results['warnings']
            }
            
            logger.info(f"File stored successfully: {final_path}")
            return storage_info
            
        except Exception as e:
            # Clean up on error
            if temp_path and os.path.exists(temp_path):
                os.unlink(temp_path)
            if final_path and os.path.exists(final_path):
                os.unlink(final_path)
            
            error_msg = f"File storage failed: {str(e)}"
            logger.error(error_msg)
            
            return {
                'success': False,
                'error': error_msg,
                'file_path': None
            }
    
    def cleanup_old_files(self, max_age_hours: int = 24) -> Dict[str, int]:
        """
        Clean up old files from upload and temp directories
        
        Args:
            max_age_hours: Maximum age in hours
            
        Returns:
            Dictionary with cleanup statistics
        """
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        cleanup_stats = {
            'uploads_cleaned': 0,
            'temp_cleaned': 0,
            'errors': 0
        }
        
        # Clean upload directories
        for upload_dir in [self.base_upload_dir / 'audio', self.base_upload_dir / 'video']:
            cleanup_stats['uploads_cleaned'] += self._cleanup_directory(upload_dir, cutoff_time)
        
        # Clean temp directory
        cleanup_stats['temp_cleaned'] = self._cleanup_directory(self.temp_dir, cutoff_time)
        
        logger.info(f"Cleanup completed: {cleanup_stats}")
        return cleanup_stats
    
    def _cleanup_directory(self, directory: Path, cutoff_time: datetime) -> int:
        """Clean up files in a directory older than cutoff time"""
        cleaned_count = 0
        
        try:
            for file_path in directory.iterdir():
                if file_path.is_file():
                    file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if file_mtime < cutoff_time:
                        try:
                            file_path.unlink()
                            cleaned_count += 1
                            logger.debug(f"Cleaned up old file: {file_path}")
                        except Exception as e:
                            logger.error(f"Failed to clean up file {file_path}: {e}")
        except Exception as e:
            logger.error(f"Error cleaning directory {directory}: {e}")
        
        return cleaned_count
    
    def get_file_info(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a stored file
        
        Args:
            file_path: Path to file
            
        Returns:
            File information dictionary or None if file not found
        """
        path = Path(file_path)
        
        if not path.exists():
            return None
        
        try:
            stat = path.stat()
            return {
                'path': str(path),
                'size_bytes': stat.st_size,
                'created_at': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                'modified_at': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'extension': path.suffix.lower()
            }
        except Exception as e:
            logger.error(f"Error getting file info for {file_path}: {e}")
            return None
    
    def delete_file(self, file_path: str) -> bool:
        """
        Safely delete a file
        
        Args:
            file_path: Path to file to delete
            
        Returns:
            True if deleted successfully
        """
        try:
            path = Path(file_path)
            if path.exists():
                path.unlink()
                logger.info(f"Deleted file: {file_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting file {file_path}: {e}")
            return False
