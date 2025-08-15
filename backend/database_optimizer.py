"""
Database optimization and monitoring for MinuteMate
Provides connection pooling, query optimization, and performance monitoring
"""

import logging
import time
import threading
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Callable
from contextlib import contextmanager
from sqlalchemy import event, text, inspect
from sqlalchemy.engine import Engine
from sqlalchemy.pool import QueuePool
from sqlalchemy.orm import sessionmaker
from models import db
import json

logger = logging.getLogger(__name__)

class DatabaseMonitor:
    """Database performance monitoring and optimization"""
    
    def __init__(self):
        self.query_stats = {}
        self.slow_queries = []
        self.connection_stats = {
            'total_connections': 0,
            'active_connections': 0,
            'failed_connections': 0,
            'connection_errors': []
        }
        self.performance_metrics = {
            'avg_query_time': 0,
            'total_queries': 0,
            'slow_query_count': 0,
            'deadlock_count': 0,
            'timeout_count': 0
        }
        self.lock = threading.Lock()
        self.slow_query_threshold = 1.0  # 1 second
        self.max_slow_queries = 100
        
    def record_query(self, query: str, duration: float, success: bool = True):
        """Record query execution statistics"""
        with self.lock:
            # Update performance metrics
            self.performance_metrics['total_queries'] += 1
            
            # Calculate rolling average
            current_avg = self.performance_metrics['avg_query_time']
            total_queries = self.performance_metrics['total_queries']
            self.performance_metrics['avg_query_time'] = (
                (current_avg * (total_queries - 1) + duration) / total_queries
            )
            
            # Record slow queries
            if duration > self.slow_query_threshold:
                self.performance_metrics['slow_query_count'] += 1
                
                slow_query = {
                    'query': query[:500],  # Truncate long queries
                    'duration': duration,
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'success': success
                }
                
                self.slow_queries.append(slow_query)
                
                # Keep only recent slow queries
                if len(self.slow_queries) > self.max_slow_queries:
                    self.slow_queries = self.slow_queries[-self.max_slow_queries:]
                
                logger.warning(f"Slow query detected ({duration:.2f}s): {query[:100]}...")
            
            # Update query statistics
            query_hash = hash(query[:200])  # Use first 200 chars for grouping
            if query_hash not in self.query_stats:
                self.query_stats[query_hash] = {
                    'query_sample': query[:200],
                    'count': 0,
                    'total_time': 0,
                    'avg_time': 0,
                    'max_time': 0,
                    'min_time': float('inf'),
                    'errors': 0
                }
            
            stats = self.query_stats[query_hash]
            stats['count'] += 1
            stats['total_time'] += duration
            stats['avg_time'] = stats['total_time'] / stats['count']
            stats['max_time'] = max(stats['max_time'], duration)
            stats['min_time'] = min(stats['min_time'], duration)
            
            if not success:
                stats['errors'] += 1
    
    def record_connection_event(self, event_type: str, details: Dict[str, Any] = None):
        """Record connection events"""
        with self.lock:
            if event_type == 'connect':
                self.connection_stats['total_connections'] += 1
                self.connection_stats['active_connections'] += 1
            elif event_type == 'disconnect':
                self.connection_stats['active_connections'] = max(0, 
                    self.connection_stats['active_connections'] - 1)
            elif event_type == 'error':
                self.connection_stats['failed_connections'] += 1
                if details:
                    error_record = {
                        'timestamp': datetime.now(timezone.utc).isoformat(),
                        'error': str(details.get('error', 'Unknown error')),
                        'details': details
                    }
                    self.connection_stats['connection_errors'].append(error_record)
                    
                    # Keep only recent errors
                    if len(self.connection_stats['connection_errors']) > 50:
                        self.connection_stats['connection_errors'] = \
                            self.connection_stats['connection_errors'][-50:]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive database statistics"""
        with self.lock:
            # Get top slow queries
            recent_slow_queries = sorted(
                self.slow_queries,
                key=lambda x: x['duration'],
                reverse=True
            )[:10]
            
            # Get most frequent queries
            top_queries = sorted(
                self.query_stats.values(),
                key=lambda x: x['count'],
                reverse=True
            )[:10]
            
            # Get slowest queries by average time
            slowest_queries = sorted(
                [q for q in self.query_stats.values() if q['count'] > 1],
                key=lambda x: x['avg_time'],
                reverse=True
            )[:10]
            
            return {
                'performance_metrics': self.performance_metrics.copy(),
                'connection_stats': self.connection_stats.copy(),
                'recent_slow_queries': recent_slow_queries,
                'top_queries_by_frequency': top_queries,
                'slowest_queries_by_avg_time': slowest_queries,
                'total_unique_queries': len(self.query_stats),
                'monitoring_since': getattr(self, 'start_time', datetime.now(timezone.utc).isoformat())
            }
    
    def reset_statistics(self):
        """Reset all statistics"""
        with self.lock:
            self.query_stats.clear()
            self.slow_queries.clear()
            self.connection_stats = {
                'total_connections': 0,
                'active_connections': 0,
                'failed_connections': 0,
                'connection_errors': []
            }
            self.performance_metrics = {
                'avg_query_time': 0,
                'total_queries': 0,
                'slow_query_count': 0,
                'deadlock_count': 0,
                'timeout_count': 0
            }
            self.start_time = datetime.now(timezone.utc).isoformat()

# Global monitor instance
db_monitor = DatabaseMonitor()

class DatabaseOptimizer:
    """Database optimization utilities"""
    
    @staticmethod
    def setup_sqlite_optimizations(engine):
        """Apply SQLite-specific optimizations"""
        try:
            with engine.connect() as conn:
                # Enable WAL mode for better concurrency
                conn.execute(text("PRAGMA journal_mode=WAL"))
                
                # Optimize SQLite settings
                conn.execute(text("PRAGMA synchronous=NORMAL"))
                conn.execute(text("PRAGMA cache_size=10000"))
                conn.execute(text("PRAGMA temp_store=MEMORY"))
                conn.execute(text("PRAGMA mmap_size=268435456"))  # 256MB
                conn.execute(text("PRAGMA foreign_keys=ON"))
                conn.execute(text("PRAGMA optimize"))
                
                conn.commit()
            
            logger.info("SQLite optimizations applied successfully")
            
        except Exception as e:
            logger.error(f"Failed to apply SQLite optimizations: {str(e)}")
    
    @staticmethod
    def setup_postgresql_optimizations(engine):
        """Apply PostgreSQL-specific optimizations"""
        try:
            with engine.connect() as conn:
                # Set connection-level optimizations
                conn.execute(text("SET statement_timeout = '30s'"))
                conn.execute(text("SET lock_timeout = '10s'"))
                conn.execute(text("SET idle_in_transaction_session_timeout = '60s'"))
                
                conn.commit()
            
            logger.info("PostgreSQL optimizations applied successfully")
            
        except Exception as e:
            logger.error(f"Failed to apply PostgreSQL optimizations: {str(e)}")
    
    @staticmethod
    def create_indexes(engine):
        """Create performance-critical indexes"""
        try:
            with engine.connect() as conn:
                # Check if indexes already exist
                inspector = inspect(engine)
                existing_indexes = set()
                
                for table_name in inspector.get_table_names():
                    for index in inspector.get_indexes(table_name):
                        existing_indexes.add(index['name'])
                
                # Define critical indexes
                indexes = [
                    "CREATE INDEX IF NOT EXISTS idx_meetings_user_id ON meetings(user_id)",
                    "CREATE INDEX IF NOT EXISTS idx_meetings_status ON meetings(status)",
                    "CREATE INDEX IF NOT EXISTS idx_meetings_created_at ON meetings(created_at)",
                    "CREATE INDEX IF NOT EXISTS idx_user_preferences_user_id ON user_preferences(user_id)",
                    "CREATE INDEX IF NOT EXISTS idx_user_preferences_category ON user_preferences(category)",
                    "CREATE INDEX IF NOT EXISTS idx_calendar_events_user_id ON calendar_events(user_id)",
                    "CREATE INDEX IF NOT EXISTS idx_calendar_events_start_time ON calendar_events(start_time)",
                    "CREATE INDEX IF NOT EXISTS idx_batch_jobs_user_id ON batch_jobs(user_id)",
                    "CREATE INDEX IF NOT EXISTS idx_batch_jobs_status ON batch_jobs(status)"
                ]
                
                for index_sql in indexes:
                    try:
                        conn.execute(text(index_sql))
                        logger.debug(f"Created index: {index_sql}")
                    except Exception as e:
                        logger.warning(f"Index creation failed (may already exist): {str(e)}")
                
                conn.commit()
            
            logger.info("Database indexes created successfully")
            
        except Exception as e:
            logger.error(f"Failed to create indexes: {str(e)}")
    
    @staticmethod
    def analyze_tables(engine):
        """Analyze tables for query optimization"""
        try:
            with engine.connect() as conn:
                if 'sqlite' in str(engine.url):
                    conn.execute(text("ANALYZE"))
                elif 'postgresql' in str(engine.url):
                    conn.execute(text("ANALYZE"))
                
                conn.commit()
            
            logger.info("Database analysis completed")
            
        except Exception as e:
            logger.error(f"Failed to analyze tables: {str(e)}")

def setup_database_monitoring(engine):
    """Set up database monitoring events"""
    
    @event.listens_for(engine, "connect")
    def receive_connect(dbapi_connection, connection_record):
        db_monitor.record_connection_event('connect')
    
    @event.listens_for(engine, "close")
    def receive_close(dbapi_connection, connection_record):
        db_monitor.record_connection_event('disconnect')
    
    @event.listens_for(engine, "before_cursor_execute")
    def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        context._query_start_time = time.time()
        context._query_statement = statement
    
    @event.listens_for(engine, "after_cursor_execute")
    def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        duration = time.time() - context._query_start_time
        db_monitor.record_query(statement, duration, success=True)
    
    @event.listens_for(engine, "dbapi_error")
    def receive_dbapi_error(exception_context):
        db_monitor.record_connection_event('error', {
            'error': str(exception_context.original_exception),
            'statement': getattr(exception_context, 'statement', None)
        })
        
        # Record failed query
        if hasattr(exception_context, 'statement'):
            db_monitor.record_query(
                exception_context.statement,
                0,  # Duration unknown for failed queries
                success=False
            )
    
    logger.info("Database monitoring events registered")

@contextmanager
def database_transaction():
    """Context manager for database transactions with monitoring"""
    start_time = time.time()
    try:
        db.session.begin()
        yield db.session
        db.session.commit()
        
        duration = time.time() - start_time
        if duration > 5.0:  # Log long transactions
            logger.warning(f"Long transaction detected: {duration:.2f}s")
            
    except Exception as e:
        db.session.rollback()
        duration = time.time() - start_time
        logger.error(f"Transaction failed after {duration:.2f}s: {str(e)}")
        raise
    finally:
        db.session.close()

def optimize_database(app, engine):
    """Apply all database optimizations"""
    try:
        # Set up monitoring
        setup_database_monitoring(engine)
        db_monitor.start_time = datetime.now(timezone.utc).isoformat()
        
        # Apply engine-specific optimizations
        if 'sqlite' in str(engine.url):
            DatabaseOptimizer.setup_sqlite_optimizations(engine)
        elif 'postgresql' in str(engine.url):
            DatabaseOptimizer.setup_postgresql_optimizations(engine)
        
        # Create performance indexes
        DatabaseOptimizer.create_indexes(engine)
        
        # Analyze tables
        DatabaseOptimizer.analyze_tables(engine)
        
        # Add database statistics endpoint
        @app.route('/api/admin/database/stats', methods=['GET'])
        def get_database_stats():
            return {
                'success': True,
                'data': db_monitor.get_statistics()
            }
        
        @app.route('/api/admin/database/reset-stats', methods=['POST'])
        def reset_database_stats():
            db_monitor.reset_statistics()
            return {
                'success': True,
                'message': 'Database statistics reset successfully'
            }
        
        logger.info("Database optimization completed successfully")
        
    except Exception as e:
        logger.error(f"Database optimization failed: {str(e)}")
        raise

def get_database_health() -> Dict[str, Any]:
    """Get database health status"""
    try:
        # Test basic connectivity
        with db.engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            result.fetchone()
        
        # Get pool status
        pool = db.engine.pool
        pool_status = {
            'size': getattr(pool, 'size', lambda: 'unknown')(),
            'checked_in': getattr(pool, 'checkedin', lambda: 'unknown')(),
            'checked_out': getattr(pool, 'checkedout', lambda: 'unknown')(),
            'overflow': getattr(pool, 'overflow', lambda: 'unknown')(),
            'invalid': getattr(pool, 'invalid', lambda: 'unknown')()
        }
        
        return {
            'status': 'healthy',
            'connection_test': 'passed',
            'pool_status': pool_status,
            'monitor_stats': db_monitor.get_statistics()
        }
        
    except Exception as e:
        return {
            'status': 'unhealthy',
            'connection_test': 'failed',
            'error': str(e),
            'monitor_stats': db_monitor.get_statistics()
        }
