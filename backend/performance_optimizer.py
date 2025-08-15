"""
Performance optimization utilities for MinuteMate
Implements caching, database optimization, and performance monitoring
"""

import logging
import time
import functools
import hashlib
import json
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Optional, Dict, List, Callable
from flask import request, g, current_app
from sqlalchemy import event, text
from sqlalchemy.engine import Engine
import redis
import pickle

logger = logging.getLogger(__name__)

class CacheManager:
    """Redis-based caching manager with fallback to in-memory cache"""
    
    def __init__(self, redis_client=None, default_ttl=3600):
        self.redis_client = redis_client
        self.default_ttl = default_ttl
        self.memory_cache = {}
        self.memory_cache_timestamps = {}
        self.use_redis = redis_client is not None
        
        if self.use_redis:
            logger.info("Using Redis for caching")
        else:
            logger.info("Using in-memory caching")
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            if self.use_redis:
                return self._get_from_redis(key)
            else:
                return self._get_from_memory(key)
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {str(e)}")
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache"""
        try:
            ttl = ttl or self.default_ttl
            
            if self.use_redis:
                return self._set_in_redis(key, value, ttl)
            else:
                return self._set_in_memory(key, value, ttl)
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {str(e)}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete value from cache"""
        try:
            if self.use_redis:
                return bool(self.redis_client.delete(key))
            else:
                if key in self.memory_cache:
                    del self.memory_cache[key]
                    del self.memory_cache_timestamps[key]
                    return True
                return False
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {str(e)}")
            return False
    
    def clear(self, pattern: str = None) -> bool:
        """Clear cache entries matching pattern"""
        try:
            if self.use_redis:
                if pattern:
                    keys = self.redis_client.keys(pattern)
                    if keys:
                        return bool(self.redis_client.delete(*keys))
                else:
                    return bool(self.redis_client.flushdb())
            else:
                if pattern:
                    import fnmatch
                    keys_to_delete = [k for k in self.memory_cache.keys() if fnmatch.fnmatch(k, pattern)]
                    for key in keys_to_delete:
                        del self.memory_cache[key]
                        del self.memory_cache_timestamps[key]
                else:
                    self.memory_cache.clear()
                    self.memory_cache_timestamps.clear()
                return True
        except Exception as e:
            logger.error(f"Cache clear error: {str(e)}")
            return False
    
    def _get_from_redis(self, key: str) -> Optional[Any]:
        """Get value from Redis"""
        data = self.redis_client.get(key)
        if data:
            return pickle.loads(data)
        return None
    
    def _set_in_redis(self, key: str, value: Any, ttl: int) -> bool:
        """Set value in Redis"""
        data = pickle.dumps(value)
        return bool(self.redis_client.setex(key, ttl, data))
    
    def _get_from_memory(self, key: str) -> Optional[Any]:
        """Get value from memory cache"""
        if key in self.memory_cache:
            timestamp = self.memory_cache_timestamps[key]
            if time.time() - timestamp < self.default_ttl:
                return self.memory_cache[key]
            else:
                # Expired
                del self.memory_cache[key]
                del self.memory_cache_timestamps[key]
        return None
    
    def _set_in_memory(self, key: str, value: Any, ttl: int) -> bool:
        """Set value in memory cache"""
        self.memory_cache[key] = value
        self.memory_cache_timestamps[key] = time.time()
        return True

class PerformanceMonitor:
    """Performance monitoring and metrics collection"""
    
    def __init__(self):
        self.request_times = []
        self.slow_queries = []
        self.cache_stats = {'hits': 0, 'misses': 0}
        self.error_counts = {}
    
    def record_request_time(self, duration: float, endpoint: str):
        """Record request processing time"""
        self.request_times.append({
            'duration': duration,
            'endpoint': endpoint,
            'timestamp': time.time()
        })
        
        # Keep only last 1000 requests
        if len(self.request_times) > 1000:
            self.request_times = self.request_times[-1000:]
        
        # Log slow requests
        if duration > 5.0:  # 5 seconds threshold
            logger.warning(f"Slow request: {endpoint} took {duration:.2f}s")
    
    def record_slow_query(self, query: str, duration: float):
        """Record slow database query"""
        self.slow_queries.append({
            'query': query[:200],  # Truncate long queries
            'duration': duration,
            'timestamp': time.time()
        })
        
        # Keep only last 100 slow queries
        if len(self.slow_queries) > 100:
            self.slow_queries = self.slow_queries[-100:]
        
        logger.warning(f"Slow query ({duration:.2f}s): {query[:100]}...")
    
    def record_cache_hit(self):
        """Record cache hit"""
        self.cache_stats['hits'] += 1
    
    def record_cache_miss(self):
        """Record cache miss"""
        self.cache_stats['misses'] += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        now = time.time()
        recent_requests = [r for r in self.request_times if now - r['timestamp'] < 3600]  # Last hour
        
        if recent_requests:
            avg_response_time = sum(r['duration'] for r in recent_requests) / len(recent_requests)
            max_response_time = max(r['duration'] for r in recent_requests)
        else:
            avg_response_time = 0
            max_response_time = 0
        
        total_cache_requests = self.cache_stats['hits'] + self.cache_stats['misses']
        cache_hit_rate = (self.cache_stats['hits'] / total_cache_requests * 100) if total_cache_requests > 0 else 0
        
        return {
            'requests_last_hour': len(recent_requests),
            'avg_response_time': round(avg_response_time, 3),
            'max_response_time': round(max_response_time, 3),
            'slow_queries_count': len(self.slow_queries),
            'cache_hit_rate': round(cache_hit_rate, 2),
            'cache_stats': self.cache_stats.copy()
        }

# Global instances
cache_manager = None
performance_monitor = PerformanceMonitor()

def cached(ttl: int = 3600, key_func: Optional[Callable] = None):
    """Decorator for caching function results"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if not cache_manager:
                # No cache available, execute function directly
                return func(*args, **kwargs)
            
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # Default key generation
                key_parts = [func.__name__]
                key_parts.extend(str(arg) for arg in args)
                key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                cache_key = hashlib.md5(":".join(key_parts).encode()).hexdigest()
            
            # Try to get from cache
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                performance_monitor.record_cache_hit()
                return cached_result
            
            # Cache miss - execute function
            performance_monitor.record_cache_miss()
            result = func(*args, **kwargs)
            
            # Store in cache
            cache_manager.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator

def cache_user_data(user_id: str, ttl: int = 1800):
    """Cache decorator for user-specific data"""
    def key_func(*args, **kwargs):
        return f"user_data:{user_id}:{args}:{kwargs}"
    
    return cached(ttl=ttl, key_func=key_func)

def cache_meeting_data(meeting_id: str, ttl: int = 3600):
    """Cache decorator for meeting-specific data"""
    def key_func(*args, **kwargs):
        return f"meeting_data:{meeting_id}:{args}:{kwargs}"
    
    return cached(ttl=ttl, key_func=key_func)

def invalidate_user_cache(user_id: str):
    """Invalidate all cached data for a user"""
    if cache_manager:
        cache_manager.clear(f"user_data:{user_id}:*")

def invalidate_meeting_cache(meeting_id: str):
    """Invalidate all cached data for a meeting"""
    if cache_manager:
        cache_manager.clear(f"meeting_data:{meeting_id}:*")

def monitor_performance(func):
    """Decorator to monitor function performance"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            duration = time.time() - start_time
            endpoint = getattr(func, '__name__', 'unknown')
            performance_monitor.record_request_time(duration, endpoint)
    
    return wrapper

def optimize_database_queries():
    """Set up database query optimization"""
    
    @event.listens_for(Engine, "before_cursor_execute")
    def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        context._query_start_time = time.time()
    
    @event.listens_for(Engine, "after_cursor_execute")
    def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        total = time.time() - context._query_start_time
        
        # Log slow queries
        if total > 1.0:  # 1 second threshold
            performance_monitor.record_slow_query(statement, total)
    
    logger.info("Database query monitoring enabled")

def setup_database_optimizations(db):
    """Set up database optimizations"""
    try:
        # Enable SQLite optimizations
        if 'sqlite' in str(db.engine.url):
            with db.engine.connect() as conn:
                # Enable WAL mode for better concurrency
                conn.execute(text("PRAGMA journal_mode=WAL"))
                
                # Optimize SQLite settings
                conn.execute(text("PRAGMA synchronous=NORMAL"))
                conn.execute(text("PRAGMA cache_size=10000"))
                conn.execute(text("PRAGMA temp_store=MEMORY"))
                conn.execute(text("PRAGMA mmap_size=268435456"))  # 256MB
                
                conn.commit()
            
            logger.info("SQLite optimizations applied")
        
        # Set up query monitoring
        optimize_database_queries()
        
    except Exception as e:
        logger.error(f"Database optimization error: {str(e)}")

def init_performance_optimization(app, redis_client=None):
    """Initialize performance optimization"""
    global cache_manager
    
    try:
        # Initialize cache manager
        cache_manager = CacheManager(redis_client)
        
        # Set up request timing middleware
        @app.before_request
        def before_request():
            g.start_time = time.time()
        
        @app.after_request
        def after_request(response):
            if hasattr(g, 'start_time'):
                duration = time.time() - g.start_time
                endpoint = request.endpoint or 'unknown'
                performance_monitor.record_request_time(duration, endpoint)
            
            return response
        
        # Add performance monitoring endpoint
        @app.route('/api/admin/performance', methods=['GET'])
        def get_performance_stats():
            return {
                'success': True,
                'data': performance_monitor.get_stats()
            }
        
        logger.info("Performance optimization initialized")
        
    except Exception as e:
        logger.error(f"Performance optimization initialization error: {str(e)}")
        raise

def compress_response(func):
    """Decorator to compress large responses"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        response = func(*args, **kwargs)
        
        # Add compression hint for large responses
        if hasattr(response, 'content_length') and response.content_length and response.content_length > 1024:
            response.headers['Vary'] = 'Accept-Encoding'
        
        return response
    
    return wrapper

def batch_database_operations(operations: List[Callable], batch_size: int = 100):
    """Execute database operations in batches for better performance"""
    results = []
    
    for i in range(0, len(operations), batch_size):
        batch = operations[i:i + batch_size]
        batch_results = []
        
        for operation in batch:
            try:
                result = operation()
                batch_results.append(result)
            except Exception as e:
                logger.error(f"Batch operation error: {str(e)}")
                batch_results.append(None)
        
        results.extend(batch_results)
    
    return results
