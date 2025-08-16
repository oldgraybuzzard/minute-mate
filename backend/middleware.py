"""
MinuteMate Middleware
Request/response middleware for logging, monitoring, and security.
"""

import os
import time
import logging
import uuid
from typing import Dict, Any, Optional
from datetime import datetime
from flask import Flask, request, g, jsonify
from werkzeug.exceptions import TooManyRequests
import threading
from collections import defaultdict, deque

logger = logging.getLogger(__name__)
access_logger = logging.getLogger('access')
security_logger = logging.getLogger('security')
performance_logger = logging.getLogger('performance')

class RateLimiter:
    """Simple in-memory rate limiter"""
    
    def __init__(self, max_requests: int = 100, window_seconds: int = 3600):
        """
        Initialize rate limiter
        
        Args:
            max_requests: Maximum requests per window
            window_seconds: Time window in seconds
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = defaultdict(deque)
        self.lock = threading.Lock()
    
    def is_allowed(self, client_id: str) -> bool:
        """
        Check if request is allowed for client
        
        Args:
            client_id: Client identifier (IP address, user ID, etc.)
            
        Returns:
            bool: True if request is allowed
        """
        now = time.time()
        
        with self.lock:
            # Clean old requests
            client_requests = self.requests[client_id]
            while client_requests and client_requests[0] < now - self.window_seconds:
                client_requests.popleft()
            
            # Check if under limit
            if len(client_requests) >= self.max_requests:
                return False
            
            # Add current request
            client_requests.append(now)
            return True
    
    def get_remaining_requests(self, client_id: str) -> int:
        """Get remaining requests for client"""
        now = time.time()
        
        with self.lock:
            client_requests = self.requests[client_id]
            # Clean old requests
            while client_requests and client_requests[0] < now - self.window_seconds:
                client_requests.popleft()
            
            return max(0, self.max_requests - len(client_requests))

class SecurityMonitor:
    """Monitor for suspicious activity"""
    
    def __init__(self):
        self.suspicious_patterns = [
            'script',
            'javascript:',
            'vbscript:',
            '<script',
            'eval(',
            'exec(',
            '../',
            '..\\',
            'union select',
            'drop table',
            'insert into'
        ]
        self.failed_attempts = defaultdict(int)
        self.lock = threading.Lock()
    
    def check_request_security(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check request for security issues
        
        Args:
            request_data: Request data to check
            
        Returns:
            Dictionary with security check results
        """
        issues = []
        
        # Check for suspicious patterns in request data
        request_str = str(request_data).lower()
        for pattern in self.suspicious_patterns:
            if pattern in request_str:
                issues.append(f"Suspicious pattern detected: {pattern}")
        
        # Check for excessively long parameters
        for key, value in request_data.items():
            if isinstance(value, str) and len(value) > 10000:
                issues.append(f"Excessively long parameter: {key}")
        
        return {
            'is_suspicious': len(issues) > 0,
            'issues': issues,
            'risk_level': 'high' if len(issues) > 2 else 'medium' if issues else 'low'
        }
    
    def record_failed_attempt(self, client_id: str):
        """Record failed authentication/validation attempt"""
        with self.lock:
            self.failed_attempts[client_id] += 1
    
    def is_blocked(self, client_id: str, threshold: int = 10) -> bool:
        """Check if client should be blocked due to failed attempts"""
        with self.lock:
            return self.failed_attempts.get(client_id, 0) >= threshold

class RequestMiddleware:
    """Comprehensive request middleware"""
    
    def __init__(self, app: Flask = None):
        """
        Initialize request middleware
        
        Args:
            app: Flask application instance
        """
        self.app = app
        self.rate_limiter = RateLimiter()
        self.security_monitor = SecurityMonitor()
        
        if app:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """
        Initialize middleware for Flask app
        
        Args:
            app: Flask application instance
        """
        self.app = app
        
        # Register middleware functions
        app.before_request(self.before_request)
        app.after_request(self.after_request)
        app.teardown_appcontext(self.teardown_request)
    
    def before_request(self):
        """Process request before handling"""
        # Generate request ID
        g.request_id = str(uuid.uuid4())[:8]
        g.start_time = time.time()
        
        # Get client information
        client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
        user_agent = request.headers.get('User-Agent', 'Unknown')
        
        # Store in request context
        g.client_ip = client_ip
        g.user_agent = user_agent
        
        # Rate limiting check
        if not self._check_rate_limit(client_ip):
            security_logger.warning(f"Rate limit exceeded for {client_ip}")
            raise TooManyRequests("Rate limit exceeded")
        
        # Security monitoring
        self._check_security()
        
        # Log request start
        logger.info(f"Request started: {request.method} {request.path}", extra={
            'request_id': g.request_id,
            'client_ip': client_ip,
            'user_agent': user_agent
        })
    
    def after_request(self, response):
        """Process response after handling"""
        # Calculate response time
        response_time = time.time() - g.start_time
        
        # Log access
        access_logger.info(
            f"{request.method} {request.path} - {response.status_code} - "
            f"{response_time:.3f}s - {g.client_ip}"
        )
        
        # Log performance if slow
        if response_time > 1.0:  # Log requests taking more than 1 second
            performance_logger.warning(
                f"Slow request: {request.method} {request.path} took {response_time:.3f}s",
                extra={
                    'request_id': g.request_id,
                    'response_time': response_time,
                    'endpoint': request.endpoint
                }
            )
        
        # Add response headers
        response.headers['X-Request-ID'] = g.request_id
        response.headers['X-Response-Time'] = f"{response_time:.3f}s"
        
        # Add rate limit headers
        remaining = self.rate_limiter.get_remaining_requests(g.client_ip)
        response.headers['X-RateLimit-Remaining'] = str(remaining)
        
        return response
    
    def teardown_request(self, exception=None):
        """Clean up after request"""
        if exception:
            logger.error(f"Request failed with exception: {str(exception)}", extra={
                'request_id': getattr(g, 'request_id', 'unknown'),
                'exception_type': type(exception).__name__
            })
    
    def _check_rate_limit(self, client_ip: str) -> bool:
        """Check rate limit for client"""
        # Check if rate limiting is disabled for development
        if os.getenv('DISABLE_RATE_LIMITING', 'false').lower() == 'true':
            return True

        # Skip rate limiting for health checks
        if request.path == '/' and request.method == 'GET':
            return True

        return self.rate_limiter.is_allowed(client_ip)
    
    def _check_security(self):
        """Perform security checks on request"""
        # Collect request data
        request_data = {}
        
        # Check query parameters
        if request.args:
            request_data.update(request.args.to_dict())
        
        # Check form data
        if request.form:
            request_data.update(request.form.to_dict())
        
        # Check JSON data
        if request.is_json:
            try:
                json_data = request.get_json()
                if json_data:
                    request_data.update(json_data)
            except Exception:
                pass  # Invalid JSON will be handled by the endpoint
        
        # Perform security check
        security_result = self.security_monitor.check_request_security(request_data)
        
        if security_result['is_suspicious']:
            security_logger.warning(
                f"Suspicious request detected from {g.client_ip}",
                extra={
                    'request_id': g.request_id,
                    'issues': security_result['issues'],
                    'risk_level': security_result['risk_level'],
                    'request_data': request_data
                }
            )
            
            # Block high-risk requests
            if security_result['risk_level'] == 'high':
                from backend.error_handlers import SecurityError
                raise SecurityError(
                    "Suspicious request detected",
                    threat_type='malicious_input',
                    source_ip=g.client_ip
                )

class HealthMonitor:
    """Monitor application health metrics"""
    
    def __init__(self):
        self.metrics = {
            'requests_total': 0,
            'requests_success': 0,
            'requests_error': 0,
            'avg_response_time': 0.0,
            'last_error': None,
            'uptime_start': datetime.now()
        }
        self.lock = threading.Lock()
    
    def record_request(self, success: bool, response_time: float, error: str = None):
        """Record request metrics"""
        with self.lock:
            self.metrics['requests_total'] += 1
            
            if success:
                self.metrics['requests_success'] += 1
            else:
                self.metrics['requests_error'] += 1
                self.metrics['last_error'] = error
            
            # Update average response time (simple moving average)
            current_avg = self.metrics['avg_response_time']
            total_requests = self.metrics['requests_total']
            self.metrics['avg_response_time'] = (
                (current_avg * (total_requests - 1) + response_time) / total_requests
            )
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get current health status"""
        with self.lock:
            uptime = datetime.now() - self.metrics['uptime_start']
            error_rate = (
                self.metrics['requests_error'] / max(self.metrics['requests_total'], 1)
            )
            
            # Determine health status
            if error_rate > 0.1:  # More than 10% error rate
                status = 'unhealthy'
            elif error_rate > 0.05:  # More than 5% error rate
                status = 'degraded'
            else:
                status = 'healthy'
            
            return {
                'status': status,
                'uptime_seconds': uptime.total_seconds(),
                'requests_total': self.metrics['requests_total'],
                'requests_success': self.metrics['requests_success'],
                'requests_error': self.metrics['requests_error'],
                'error_rate': error_rate,
                'avg_response_time': self.metrics['avg_response_time'],
                'last_error': self.metrics['last_error']
            }

# Global instances
health_monitor = HealthMonitor()

def setup_middleware(app: Flask) -> RequestMiddleware:
    """
    Setup middleware for Flask application
    
    Args:
        app: Flask application instance
        
    Returns:
        RequestMiddleware instance
    """
    middleware = RequestMiddleware(app)
    
    # Add health monitoring endpoint
    @app.route('/api/health/detailed')
    def detailed_health():
        """Detailed health check endpoint"""
        health_status = health_monitor.get_health_status()
        return jsonify(health_status)
    
    return middleware
