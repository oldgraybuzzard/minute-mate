"""
MinuteMate Logging Configuration
Advanced logging setup with multiple handlers, formatters, and log levels.
"""

import os
import logging
import logging.handlers
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

class ColoredFormatter(logging.Formatter):
    """Custom formatter with color coding for console output"""
    
    # Color codes for different log levels
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m'      # Reset
    }
    
    def format(self, record):
        # Add color to levelname
        if record.levelname in self.COLORS:
            record.levelname = f"{self.COLORS[record.levelname]}{record.levelname}{self.COLORS['RESET']}"
        
        return super().format(record)

class RequestContextFilter(logging.Filter):
    """Filter to add request context to log records"""
    
    def filter(self, record):
        # Add request ID if available (would need Flask-Request-ID or similar)
        record.request_id = getattr(record, 'request_id', 'N/A')
        
        # Add user info if available
        record.user_id = getattr(record, 'user_id', 'anonymous')
        
        return True

class LoggingManager:
    """Manages application logging configuration"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize logging manager
        
        Args:
            config: Application configuration dictionary
        """
        self.config = config
        self.log_dir = Path(config.get('LOG_DIR', 'logs'))
        self.log_level = config.get('LOG_LEVEL', 'INFO')
        self.max_file_size = config.get('LOG_MAX_FILE_SIZE', 10 * 1024 * 1024)  # 10MB
        self.backup_count = config.get('LOG_BACKUP_COUNT', 5)
        self.enable_console = config.get('LOG_ENABLE_CONSOLE', True)
        self.enable_file = config.get('LOG_ENABLE_FILE', True)
        
        # Ensure log directory exists
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self._setup_logging()
    
    def _setup_logging(self):
        """Setup logging configuration"""
        # Clear any existing handlers
        root_logger = logging.getLogger()
        root_logger.handlers.clear()
        
        # Set root logger level
        root_logger.setLevel(getattr(logging, self.log_level.upper()))
        
        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(request_id)s - %(user_id)s - %(message)s'
        )
        
        simple_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        
        colored_formatter = ColoredFormatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Add request context filter
        context_filter = RequestContextFilter()
        
        # Setup console handler
        if self.enable_console:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(getattr(logging, self.log_level.upper()))
            console_handler.setFormatter(colored_formatter)
            root_logger.addHandler(console_handler)
        
        # Setup file handlers
        if self.enable_file:
            # Main application log
            app_log_file = self.log_dir / 'minutemate.log'
            app_handler = logging.handlers.RotatingFileHandler(
                app_log_file,
                maxBytes=self.max_file_size,
                backupCount=self.backup_count
            )
            app_handler.setLevel(logging.INFO)
            app_handler.setFormatter(detailed_formatter)
            app_handler.addFilter(context_filter)
            root_logger.addHandler(app_handler)
            
            # Error log (errors and above only)
            error_log_file = self.log_dir / 'errors.log'
            error_handler = logging.handlers.RotatingFileHandler(
                error_log_file,
                maxBytes=self.max_file_size,
                backupCount=self.backup_count
            )
            error_handler.setLevel(logging.ERROR)
            error_handler.setFormatter(detailed_formatter)
            error_handler.addFilter(context_filter)
            root_logger.addHandler(error_handler)
            
            # Access log for API requests
            access_log_file = self.log_dir / 'access.log'
            access_handler = logging.handlers.RotatingFileHandler(
                access_log_file,
                maxBytes=self.max_file_size,
                backupCount=self.backup_count
            )
            access_handler.setLevel(logging.INFO)
            access_handler.setFormatter(simple_formatter)
            
            # Create access logger
            access_logger = logging.getLogger('access')
            access_logger.addHandler(access_handler)
            access_logger.setLevel(logging.INFO)
            access_logger.propagate = False
        
        logging.info("Logging configuration initialized")
    
    def get_logger(self, name: str) -> logging.Logger:
        """
        Get a logger with the specified name
        
        Args:
            name: Logger name
            
        Returns:
            Configured logger instance
        """
        return logging.getLogger(name)
    
    def log_request(self, method: str, path: str, status_code: int, 
                   response_time: float, user_id: str = 'anonymous'):
        """
        Log API request
        
        Args:
            method: HTTP method
            path: Request path
            status_code: Response status code
            response_time: Response time in seconds
            user_id: User identifier
        """
        access_logger = logging.getLogger('access')
        access_logger.info(
            f"{method} {path} - {status_code} - {response_time:.3f}s - {user_id}"
        )
    
    def log_error(self, error: Exception, context: Optional[Dict[str, Any]] = None,
                 user_id: str = 'anonymous', request_id: str = 'N/A'):
        """
        Log error with context
        
        Args:
            error: Exception object
            context: Additional context information
            user_id: User identifier
            request_id: Request identifier
        """
        logger = logging.getLogger('error')
        
        error_msg = f"Error: {str(error)}"
        if context:
            error_msg += f" | Context: {context}"
        
        # Add extra fields for filtering
        extra = {
            'user_id': user_id,
            'request_id': request_id,
            'error_type': type(error).__name__
        }
        
        logger.error(error_msg, extra=extra, exc_info=True)
    
    def log_security_event(self, event_type: str, details: Dict[str, Any],
                          severity: str = 'WARNING', user_id: str = 'anonymous'):
        """
        Log security-related events
        
        Args:
            event_type: Type of security event
            details: Event details
            severity: Log severity level
            user_id: User identifier
        """
        security_logger = logging.getLogger('security')
        
        message = f"Security Event: {event_type} | Details: {details}"
        
        extra = {
            'user_id': user_id,
            'event_type': event_type,
            'security_event': True
        }
        
        level = getattr(logging, severity.upper(), logging.WARNING)
        security_logger.log(level, message, extra=extra)
    
    def log_performance(self, operation: str, duration: float, 
                       details: Optional[Dict[str, Any]] = None):
        """
        Log performance metrics
        
        Args:
            operation: Operation name
            duration: Operation duration in seconds
            details: Additional details
        """
        perf_logger = logging.getLogger('performance')
        
        message = f"Performance: {operation} took {duration:.3f}s"
        if details:
            message += f" | Details: {details}"
        
        extra = {
            'operation': operation,
            'duration': duration,
            'performance_metric': True
        }
        
        perf_logger.info(message, extra=extra)

def setup_logging(config: Dict[str, Any]) -> LoggingManager:
    """
    Setup application logging
    
    Args:
        config: Application configuration
        
    Returns:
        LoggingManager instance
    """
    return LoggingManager(config)

def get_request_logger() -> logging.Logger:
    """Get logger for request handling"""
    return logging.getLogger('request')

def get_security_logger() -> logging.Logger:
    """Get logger for security events"""
    return logging.getLogger('security')

def get_performance_logger() -> logging.Logger:
    """Get logger for performance metrics"""
    return logging.getLogger('performance')

def get_error_logger() -> logging.Logger:
    """Get logger for error handling"""
    return logging.getLogger('error')
