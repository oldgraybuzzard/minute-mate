"""
MinuteMate Error Handlers
Comprehensive error handling with custom exceptions and user-friendly responses.
"""

import logging
import traceback
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
from flask import Flask, request, jsonify
from werkzeug.exceptions import HTTPException, RequestEntityTooLarge, BadRequest
import uuid

logger = logging.getLogger(__name__)

# Custom Exception Classes
class MinuteMateError(Exception):
    """Base exception for MinuteMate application"""
    
    def __init__(self, message: str, error_code: str = None, details: Dict[str, Any] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or 'GENERAL_ERROR'
        self.details = details or {}
        self.timestamp = datetime.now().isoformat()

class ValidationError(MinuteMateError):
    """Exception for validation errors"""
    
    def __init__(self, message: str, field: str = None, value: Any = None):
        super().__init__(message, 'VALIDATION_ERROR')
        self.field = field
        self.value = value
        if field:
            self.details['field'] = field
        if value is not None:
            self.details['value'] = str(value)

class FileProcessingError(MinuteMateError):
    """Exception for file processing errors"""
    
    def __init__(self, message: str, file_path: str = None, operation: str = None):
        super().__init__(message, 'FILE_PROCESSING_ERROR')
        self.file_path = file_path
        self.operation = operation
        if file_path:
            self.details['file_path'] = file_path
        if operation:
            self.details['operation'] = operation

class TranscriptionError(MinuteMateError):
    """Exception for transcription errors"""
    
    def __init__(self, message: str, model: str = None, language: str = None):
        super().__init__(message, 'TRANSCRIPTION_ERROR')
        self.model = model
        self.language = language
        if model:
            self.details['model'] = model
        if language:
            self.details['language'] = language

class SecurityError(MinuteMateError):
    """Exception for security-related errors"""
    
    def __init__(self, message: str, threat_type: str = None, source_ip: str = None):
        super().__init__(message, 'SECURITY_ERROR')
        self.threat_type = threat_type
        self.source_ip = source_ip
        if threat_type:
            self.details['threat_type'] = threat_type
        if source_ip:
            self.details['source_ip'] = source_ip

class ResourceError(MinuteMateError):
    """Exception for resource-related errors (disk space, memory, etc.)"""
    
    def __init__(self, message: str, resource_type: str = None, current_usage: str = None):
        super().__init__(message, 'RESOURCE_ERROR')
        self.resource_type = resource_type
        self.current_usage = current_usage
        if resource_type:
            self.details['resource_type'] = resource_type
        if current_usage:
            self.details['current_usage'] = current_usage

class ConfigurationError(MinuteMateError):
    """Exception for configuration errors"""
    
    def __init__(self, message: str, config_key: str = None, expected_type: str = None):
        super().__init__(message, 'CONFIGURATION_ERROR')
        self.config_key = config_key
        self.expected_type = expected_type
        if config_key:
            self.details['config_key'] = config_key
        if expected_type:
            self.details['expected_type'] = expected_type

class ErrorHandler:
    """Centralized error handling and response generation"""
    
    def __init__(self, app: Flask = None):
        """
        Initialize error handler
        
        Args:
            app: Flask application instance
        """
        self.app = app
        self.error_logger = logging.getLogger('error')
        self.security_logger = logging.getLogger('security')
        
        if app:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """
        Initialize error handling for Flask app
        
        Args:
            app: Flask application instance
        """
        self.app = app
        
        # Register error handlers
        app.errorhandler(ValidationError)(self.handle_validation_error)
        app.errorhandler(FileProcessingError)(self.handle_file_processing_error)
        app.errorhandler(TranscriptionError)(self.handle_transcription_error)
        app.errorhandler(SecurityError)(self.handle_security_error)
        app.errorhandler(ResourceError)(self.handle_resource_error)
        app.errorhandler(ConfigurationError)(self.handle_configuration_error)
        app.errorhandler(MinuteMateError)(self.handle_minutemate_error)
        
        # Standard HTTP errors
        app.errorhandler(400)(self.handle_bad_request)
        app.errorhandler(401)(self.handle_unauthorized)
        app.errorhandler(403)(self.handle_forbidden)
        app.errorhandler(404)(self.handle_not_found)
        app.errorhandler(405)(self.handle_method_not_allowed)
        app.errorhandler(413)(self.handle_request_entity_too_large)
        app.errorhandler(429)(self.handle_too_many_requests)
        app.errorhandler(500)(self.handle_internal_server_error)
        app.errorhandler(503)(self.handle_service_unavailable)
        
        # Generic exception handler
        app.errorhandler(Exception)(self.handle_generic_exception)
    
    def _generate_error_id(self) -> str:
        """Generate unique error ID for tracking"""
        return str(uuid.uuid4())[:8]
    
    def _create_error_response(self, error_code: str, message: str, 
                             status_code: int, details: Dict[str, Any] = None,
                             error_id: str = None) -> Tuple[Dict[str, Any], int]:
        """
        Create standardized error response
        
        Args:
            error_code: Error code
            message: Error message
            status_code: HTTP status code
            details: Additional error details
            error_id: Unique error identifier
            
        Returns:
            Tuple of (response_dict, status_code)
        """
        error_id = error_id or self._generate_error_id()
        
        response = {
            'success': False,
            'error': {
                'code': error_code,
                'message': message,
                'error_id': error_id,
                'timestamp': datetime.now().isoformat()
            }
        }
        
        if details:
            response['error']['details'] = details
        
        # Add helpful information for development
        if self.app and self.app.config.get('DEBUG'):
            response['error']['debug_info'] = {
                'request_method': request.method if request else 'N/A',
                'request_path': request.path if request else 'N/A',
                'user_agent': request.headers.get('User-Agent') if request else 'N/A'
            }
        
        return response, status_code
    
    def handle_validation_error(self, error: ValidationError):
        """Handle validation errors"""
        self.error_logger.warning(f"Validation error: {error.message}", extra={
            'error_code': error.error_code,
            'field': error.field,
            'value': error.value
        })
        
        return jsonify(*self._create_error_response(
            error_code=error.error_code,
            message=error.message,
            status_code=400,
            details=error.details
        ))
    
    def handle_file_processing_error(self, error: FileProcessingError):
        """Handle file processing errors"""
        self.error_logger.error(f"File processing error: {error.message}", extra={
            'error_code': error.error_code,
            'file_path': error.file_path,
            'operation': error.operation
        })
        
        return jsonify(*self._create_error_response(
            error_code=error.error_code,
            message="File processing failed. Please check your file and try again.",
            status_code=422,
            details=error.details
        ))
    
    def handle_transcription_error(self, error: TranscriptionError):
        """Handle transcription errors"""
        self.error_logger.error(f"Transcription error: {error.message}", extra={
            'error_code': error.error_code,
            'model': error.model,
            'language': error.language
        })
        
        return jsonify(*self._create_error_response(
            error_code=error.error_code,
            message="Transcription failed. Please try again or contact support.",
            status_code=422,
            details=error.details
        ))
    
    def handle_security_error(self, error: SecurityError):
        """Handle security errors"""
        # Log security events with high priority
        self.security_logger.error(f"Security error: {error.message}", extra={
            'error_code': error.error_code,
            'threat_type': error.threat_type,
            'source_ip': error.source_ip or (request.remote_addr if request else 'unknown')
        })
        
        return jsonify(*self._create_error_response(
            error_code=error.error_code,
            message="Security validation failed.",
            status_code=403,
            details={'threat_detected': True}
        ))
    
    def handle_resource_error(self, error: ResourceError):
        """Handle resource errors"""
        self.error_logger.error(f"Resource error: {error.message}", extra={
            'error_code': error.error_code,
            'resource_type': error.resource_type,
            'current_usage': error.current_usage
        })
        
        return jsonify(*self._create_error_response(
            error_code=error.error_code,
            message="System resources temporarily unavailable. Please try again later.",
            status_code=503,
            details=error.details
        ))
    
    def handle_configuration_error(self, error: ConfigurationError):
        """Handle configuration errors"""
        self.error_logger.critical(f"Configuration error: {error.message}", extra={
            'error_code': error.error_code,
            'config_key': error.config_key,
            'expected_type': error.expected_type
        })
        
        return jsonify(*self._create_error_response(
            error_code=error.error_code,
            message="Service configuration error. Please contact support.",
            status_code=500,
            details={'contact_support': True}
        ))
    
    def handle_minutemate_error(self, error: MinuteMateError):
        """Handle generic MinuteMate errors"""
        self.error_logger.error(f"MinuteMate error: {error.message}", extra={
            'error_code': error.error_code,
            'details': error.details
        })
        
        return jsonify(*self._create_error_response(
            error_code=error.error_code,
            message=error.message,
            status_code=500,
            details=error.details
        ))
    
    def handle_bad_request(self, error):
        """Handle 400 Bad Request errors"""
        return jsonify(*self._create_error_response(
            error_code='BAD_REQUEST',
            message='Invalid request format or parameters.',
            status_code=400
        ))
    
    def handle_unauthorized(self, error):
        """Handle 401 Unauthorized errors"""
        return jsonify(*self._create_error_response(
            error_code='UNAUTHORIZED',
            message='Authentication required.',
            status_code=401
        ))
    
    def handle_forbidden(self, error):
        """Handle 403 Forbidden errors"""
        return jsonify(*self._create_error_response(
            error_code='FORBIDDEN',
            message='Access denied.',
            status_code=403
        ))
    
    def handle_not_found(self, error):
        """Handle 404 Not Found errors"""
        return jsonify(*self._create_error_response(
            error_code='NOT_FOUND',
            message='The requested resource was not found.',
            status_code=404
        ))
    
    def handle_method_not_allowed(self, error):
        """Handle 405 Method Not Allowed errors"""
        return jsonify(*self._create_error_response(
            error_code='METHOD_NOT_ALLOWED',
            message='HTTP method not allowed for this endpoint.',
            status_code=405
        ))
    
    def handle_request_entity_too_large(self, error):
        """Handle 413 Request Entity Too Large errors"""
        max_size = self.app.config.get('MAX_CONTENT_LENGTH', 0) // (1024 * 1024)
        return jsonify(*self._create_error_response(
            error_code='FILE_TOO_LARGE',
            message=f'File size exceeds maximum limit of {max_size}MB.',
            status_code=413,
            details={'max_size_mb': max_size}
        ))
    
    def handle_too_many_requests(self, error):
        """Handle 429 Too Many Requests errors"""
        return jsonify(*self._create_error_response(
            error_code='RATE_LIMIT_EXCEEDED',
            message='Too many requests. Please try again later.',
            status_code=429
        ))
    
    def handle_internal_server_error(self, error):
        """Handle 500 Internal Server Error"""
        error_id = self._generate_error_id()
        
        self.error_logger.error(f"Internal server error: {str(error)}", extra={
            'error_id': error_id,
            'traceback': traceback.format_exc()
        })
        
        return jsonify(*self._create_error_response(
            error_code='INTERNAL_SERVER_ERROR',
            message='An internal server error occurred. Please try again later.',
            status_code=500,
            error_id=error_id
        ))
    
    def handle_service_unavailable(self, error):
        """Handle 503 Service Unavailable errors"""
        return jsonify(*self._create_error_response(
            error_code='SERVICE_UNAVAILABLE',
            message='Service temporarily unavailable. Please try again later.',
            status_code=503
        ))
    
    def handle_generic_exception(self, error: Exception):
        """Handle any unhandled exceptions"""
        error_id = self._generate_error_id()
        
        self.error_logger.error(f"Unhandled exception: {str(error)}", extra={
            'error_id': error_id,
            'error_type': type(error).__name__,
            'traceback': traceback.format_exc()
        })
        
        # Don't expose internal error details in production
        if self.app and not self.app.config.get('DEBUG'):
            message = 'An unexpected error occurred. Please try again later.'
        else:
            message = f'Unhandled exception: {str(error)}'
        
        return jsonify(*self._create_error_response(
            error_code='UNHANDLED_EXCEPTION',
            message=message,
            status_code=500,
            error_id=error_id
        ))
