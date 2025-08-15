"""
Security middleware for MinuteMate
Implements rate limiting, request validation, and security headers
"""

import logging
import time
import hashlib
import json
from datetime import datetime, timedelta, timezone
from functools import wraps
from collections import defaultdict, deque
from flask import request, jsonify, current_app, g
from werkzeug.exceptions import TooManyRequests
import redis
import os
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)

class RateLimiter:
    """Rate limiting implementation with Redis backend"""
    
    def __init__(self, redis_client=None):
        self.redis_client = redis_client
        self.memory_store = defaultdict(deque)  # Fallback for when Redis is not available
        self.use_redis = redis_client is not None
        
    def is_allowed(self, key: str, limit: int, window: int) -> Tuple[bool, Dict]:
        """
        Check if request is allowed based on rate limit
        
        Args:
            key: Unique identifier for the rate limit (e.g., IP address, user ID)
            limit: Maximum number of requests allowed
            window: Time window in seconds
            
        Returns:
            Tuple of (is_allowed, info_dict)
        """
        now = time.time()
        
        if self.use_redis:
            return self._check_redis_rate_limit(key, limit, window, now)
        else:
            return self._check_memory_rate_limit(key, limit, window, now)
    
    def _check_redis_rate_limit(self, key: str, limit: int, window: int, now: float) -> Tuple[bool, Dict]:
        """Check rate limit using Redis"""
        try:
            pipe = self.redis_client.pipeline()
            
            # Remove old entries
            pipe.zremrangebyscore(key, 0, now - window)
            
            # Count current requests
            pipe.zcard(key)
            
            # Add current request
            pipe.zadd(key, {str(now): now})
            
            # Set expiration
            pipe.expire(key, window)
            
            results = pipe.execute()
            current_requests = results[1]
            
            if current_requests < limit:
                return True, {
                    'allowed': True,
                    'current_requests': current_requests + 1,
                    'limit': limit,
                    'window': window,
                    'reset_time': now + window
                }
            else:
                # Remove the request we just added since it's not allowed
                self.redis_client.zrem(key, str(now))
                
                # Get the oldest request time to calculate reset time
                oldest = self.redis_client.zrange(key, 0, 0, withscores=True)
                reset_time = oldest[0][1] + window if oldest else now + window
                
                return False, {
                    'allowed': False,
                    'current_requests': current_requests,
                    'limit': limit,
                    'window': window,
                    'reset_time': reset_time,
                    'retry_after': reset_time - now
                }
                
        except Exception as e:
            logger.error(f"Redis rate limiting error: {str(e)}")
            # Fallback to memory-based rate limiting
            return self._check_memory_rate_limit(key, limit, window, now)
    
    def _check_memory_rate_limit(self, key: str, limit: int, window: int, now: float) -> Tuple[bool, Dict]:
        """Check rate limit using in-memory storage"""
        requests = self.memory_store[key]
        
        # Remove old requests
        while requests and requests[0] <= now - window:
            requests.popleft()
        
        if len(requests) < limit:
            requests.append(now)
            return True, {
                'allowed': True,
                'current_requests': len(requests),
                'limit': limit,
                'window': window,
                'reset_time': now + window
            }
        else:
            reset_time = requests[0] + window
            return False, {
                'allowed': False,
                'current_requests': len(requests),
                'limit': limit,
                'window': window,
                'reset_time': reset_time,
                'retry_after': reset_time - now
            }

class SecurityMiddleware:
    """Security middleware for request validation and protection"""
    
    def __init__(self, app=None, redis_client=None):
        self.app = app
        self.rate_limiter = RateLimiter(redis_client)
        self.blocked_ips = set()
        self.suspicious_patterns = [
            r'<script',
            r'javascript:',
            r'onload=',
            r'onerror=',
            r'eval\(',
            r'document\.cookie',
            r'window\.location',
            r'\.\./',
            r'union.*select',
            r'drop.*table',
            r'insert.*into',
            r'delete.*from'
        ]
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize security middleware with Flask app"""
        self.app = app
        
        # Register before_request handler
        app.before_request(self.before_request)
        
        # Register after_request handler for security headers
        app.after_request(self.after_request)
        
        logger.info("Security middleware initialized")
    
    def before_request(self):
        """Process request before routing"""
        try:
            # Skip security checks for static files
            if request.endpoint and request.endpoint.startswith('static'):
                return
            
            # Check if IP is blocked
            if self._is_ip_blocked(request.remote_addr):
                logger.warning(f"Blocked IP attempted access: {request.remote_addr}")
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'IP_BLOCKED',
                        'message': 'Access denied'
                    }
                }), 403
            
            # Apply rate limiting
            rate_limit_result = self._apply_rate_limiting()
            if rate_limit_result:
                return rate_limit_result
            
            # Validate request content
            validation_result = self._validate_request_content()
            if validation_result:
                return validation_result
            
            # Log request for monitoring
            self._log_request()
            
        except Exception as e:
            logger.error(f"Security middleware error: {str(e)}")
            # Don't block requests due to security middleware errors
            pass
    
    def after_request(self, response):
        """Add security headers to response"""
        try:
            # Security headers
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['X-Frame-Options'] = 'DENY'
            response.headers['X-XSS-Protection'] = '1; mode=block'
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
            response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
            
            # Content Security Policy
            csp = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com; "
                "style-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com; "
                "img-src 'self' data: https:; "
                "font-src 'self' https://cdnjs.cloudflare.com; "
                "connect-src 'self'; "
                "frame-ancestors 'none'"
            )
            response.headers['Content-Security-Policy'] = csp
            
            # Add rate limit headers if available
            if hasattr(g, 'rate_limit_info'):
                info = g.rate_limit_info
                response.headers['X-RateLimit-Limit'] = str(info['limit'])
                response.headers['X-RateLimit-Remaining'] = str(max(0, info['limit'] - info['current_requests']))
                response.headers['X-RateLimit-Reset'] = str(int(info['reset_time']))
                
                if not info['allowed']:
                    response.headers['Retry-After'] = str(int(info.get('retry_after', 60)))
            
        except Exception as e:
            logger.error(f"Error adding security headers: {str(e)}")
        
        return response
    
    def _is_ip_blocked(self, ip_address: str) -> bool:
        """Check if IP address is blocked"""
        return ip_address in self.blocked_ips
    
    def _apply_rate_limiting(self):
        """Apply rate limiting based on request type and user"""
        try:
            # Check if rate limiting is disabled
            if os.getenv('DISABLE_RATE_LIMITING', 'false').lower() == 'true':
                return None

            # Get rate limit configuration
            endpoint = request.endpoint or 'unknown'
            
            # Different limits for different endpoints - More generous for production
            rate_limits = {
                'auth.login': (10, 300),  # 10 attempts per 5 minutes
                'auth.register': (5, 3600),  # 5 attempts per hour
                'upload': (20, 3600),  # 20 uploads per hour
                'api.upload': (20, 3600),
                'doc_comparison.upload_edited_document': (10, 3600),  # 10 document comparisons per hour
                'serve_frontend': (1000, 3600),  # 1000 frontend requests per hour
                'serve_frontend_files': (1000, 3600),  # 1000 static file requests per hour
                'comprehensive_health_check': (200, 3600),  # 200 health checks per hour
                'index': (500, 3600),  # 500 main page requests per hour
                'default': (500, 3600)  # 500 requests per hour for other endpoints
            }
            
            # Special handling for frontend routes
            if request.path.startswith('/frontend'):
                if request.path.endswith(('.css', '.js', '.png', '.jpg', '.ico')):
                    limit, window = rate_limits['serve_frontend_files']
                else:
                    limit, window = rate_limits['serve_frontend']
            else:
                limit, window = rate_limits.get(endpoint, rate_limits['default'])
            
            # Create rate limit key
            user_id = getattr(g, 'current_user_id', None) if hasattr(g, 'current_user_id') else None
            if user_id:
                key = f"rate_limit:user:{user_id}:{endpoint}"
            else:
                key = f"rate_limit:ip:{request.remote_addr}:{endpoint}"
            
            # Check rate limit
            allowed, info = self.rate_limiter.is_allowed(key, limit, window)
            g.rate_limit_info = info
            
            if not allowed:
                logger.warning(f"Rate limit exceeded for {request.remote_addr} on endpoint '{endpoint}' (key: {key})")
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'RATE_LIMIT_EXCEEDED',
                        'message': f'Rate limit exceeded. Try again in {int(info.get("retry_after", 60))} seconds.',
                        'retry_after': int(info.get('retry_after', 60))
                    }
                }), 429
            
        except Exception as e:
            logger.error(f"Rate limiting error: {str(e)}")
        
        return None
    
    def _validate_request_content(self):
        """Validate request content for security threats"""
        try:
            # Check request size
            max_content_length = current_app.config.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024)  # 16MB default
            if request.content_length and request.content_length > max_content_length:
                logger.warning(f"Request too large: {request.content_length} bytes from {request.remote_addr}")
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'REQUEST_TOO_LARGE',
                        'message': 'Request entity too large'
                    }
                }), 413
            
            # Check for suspicious patterns in URL and query parameters
            suspicious_content = []
            
            # Check URL path
            if self._contains_suspicious_patterns(request.path):
                suspicious_content.append('URL path')
            
            # Check query parameters
            for key, value in request.args.items():
                if self._contains_suspicious_patterns(f"{key}={value}"):
                    suspicious_content.append(f'Query parameter: {key}')
            
            # Check JSON body for POST/PUT requests
            if request.method in ['POST', 'PUT', 'PATCH'] and request.is_json:
                try:
                    data = request.get_json()
                    if data and self._contains_suspicious_patterns(json.dumps(data)):
                        suspicious_content.append('Request body')
                except Exception:
                    pass  # Invalid JSON will be handled by route validation
            
            if suspicious_content:
                logger.warning(f"Suspicious content detected from {request.remote_addr}: {suspicious_content}")
                self._record_suspicious_activity(request.remote_addr)
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'SUSPICIOUS_CONTENT',
                        'message': 'Request contains suspicious content'
                    }
                }), 400
            
        except Exception as e:
            logger.error(f"Content validation error: {str(e)}")
        
        return None
    
    def _contains_suspicious_patterns(self, content: str) -> bool:
        """Check if content contains suspicious patterns"""
        import re
        content_lower = content.lower()
        
        for pattern in self.suspicious_patterns:
            if re.search(pattern, content_lower, re.IGNORECASE):
                return True
        
        return False
    
    def _record_suspicious_activity(self, ip_address: str):
        """Record suspicious activity and potentially block IP"""
        # In a production system, this would integrate with a threat detection system
        # For now, we'll just log it
        logger.warning(f"Suspicious activity recorded for IP: {ip_address}")
        
        # Could implement automatic IP blocking after multiple suspicious requests
        # self.blocked_ips.add(ip_address)
    
    def _log_request(self):
        """Log request for monitoring and analytics"""
        try:
            log_data = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'method': request.method,
                'url': request.url,
                'endpoint': request.endpoint,
                'ip_address': request.remote_addr,
                'user_agent': request.headers.get('User-Agent'),
                'content_length': request.content_length,
                'referrer': request.headers.get('Referer')
            }
            
            # Add user info if available
            if hasattr(g, 'current_user_id'):
                log_data['user_id'] = g.current_user_id
            
            # Log at debug level to avoid spam
            logger.debug(f"Request: {json.dumps(log_data)}")
            
        except Exception as e:
            logger.error(f"Request logging error: {str(e)}")

def create_redis_client():
    """Create Redis client for rate limiting"""
    try:
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        client = redis.from_url(redis_url, decode_responses=True)
        
        # Test connection
        client.ping()
        logger.info("Redis client created successfully")
        return client
        
    except Exception as e:
        logger.warning(f"Could not connect to Redis: {str(e)}. Using in-memory rate limiting.")
        return None

def init_security(app):
    """Initialize security middleware"""
    try:
        # Create Redis client
        redis_client = create_redis_client()
        
        # Initialize security middleware
        security = SecurityMiddleware(app, redis_client)
        
        # Set security configuration
        app.config.setdefault('MAX_CONTENT_LENGTH', 100 * 1024 * 1024)  # 100MB max request size
        
        logger.info("Security middleware initialized successfully")
        return security
        
    except Exception as e:
        logger.error(f"Failed to initialize security middleware: {str(e)}")
        raise
