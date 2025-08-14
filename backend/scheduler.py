"""
MinuteMate Background Scheduler
Handles background tasks like file cleanup and maintenance.
"""

import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Optional, Callable

logger = logging.getLogger(__name__)

class BackgroundScheduler:
    """Simple background task scheduler"""
    
    def __init__(self):
        self.tasks = []
        self.running = False
        self.thread = None
        self._stop_event = threading.Event()
        logger.info("BackgroundScheduler initialized")
    
    def add_task(self, name: str, func: Callable, interval_seconds: int, 
                 run_immediately: bool = False):
        """
        Add a recurring task
        
        Args:
            name: Task name
            func: Function to execute
            interval_seconds: Interval between executions
            run_immediately: Whether to run the task immediately
        """
        task = {
            'name': name,
            'func': func,
            'interval': interval_seconds,
            'last_run': None if not run_immediately else datetime.now() - timedelta(seconds=interval_seconds),
            'next_run': datetime.now() if run_immediately else datetime.now() + timedelta(seconds=interval_seconds)
        }
        self.tasks.append(task)
        logger.info(f"Added task: {name} (interval: {interval_seconds}s)")
    
    def start(self):
        """Start the scheduler"""
        if self.running:
            logger.warning("Scheduler is already running")
            return
        
        self.running = True
        self._stop_event.clear()
        self.thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.thread.start()
        logger.info("Background scheduler started")
    
    def stop(self):
        """Stop the scheduler"""
        if not self.running:
            return
        
        self.running = False
        self._stop_event.set()
        
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5)
        
        logger.info("Background scheduler stopped")
    
    def _run_scheduler(self):
        """Main scheduler loop"""
        while self.running and not self._stop_event.is_set():
            try:
                current_time = datetime.now()
                
                for task in self.tasks:
                    if current_time >= task['next_run']:
                        self._execute_task(task)
                        
                        # Schedule next run
                        task['last_run'] = current_time
                        task['next_run'] = current_time + timedelta(seconds=task['interval'])
                
                # Sleep for a short interval before checking again
                self._stop_event.wait(timeout=60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                time.sleep(60)  # Wait before retrying
    
    def _execute_task(self, task):
        """Execute a single task"""
        try:
            logger.info(f"Executing task: {task['name']}")
            task['func']()
            logger.info(f"Task completed: {task['name']}")
        except Exception as e:
            logger.error(f"Task failed: {task['name']} - {e}")

class FileCleanupScheduler:
    """Specialized scheduler for file cleanup tasks"""
    
    def __init__(self, file_storage_manager, job_tracker, config):
        """
        Initialize file cleanup scheduler
        
        Args:
            file_storage_manager: FileStorageManager instance
            job_tracker: JobTracker instance
            config: Application configuration
        """
        self.file_storage = file_storage_manager
        self.job_tracker = job_tracker
        self.config = config
        self.scheduler = BackgroundScheduler()
        
        # Setup cleanup tasks if auto cleanup is enabled
        if config.get('AUTO_CLEANUP_ENABLED', True):
            self._setup_cleanup_tasks()
        
        logger.info("FileCleanupScheduler initialized")
    
    def _setup_cleanup_tasks(self):
        """Setup automatic cleanup tasks"""
        cleanup_interval = self.config.get('CLEANUP_INTERVAL_HOURS', 6) * 3600  # Convert to seconds
        
        # Add file cleanup task
        self.scheduler.add_task(
            name="file_cleanup",
            func=self._cleanup_files,
            interval_seconds=cleanup_interval,
            run_immediately=False
        )
        
        # Add job cleanup task
        self.scheduler.add_task(
            name="job_cleanup", 
            func=self._cleanup_jobs,
            interval_seconds=cleanup_interval,
            run_immediately=False
        )
        
        # Add temp file cleanup (more frequent)
        temp_cleanup_interval = self.config.get('TEMP_FILE_AGE_HOURS', 2) * 3600
        self.scheduler.add_task(
            name="temp_cleanup",
            func=self._cleanup_temp_files,
            interval_seconds=temp_cleanup_interval,
            run_immediately=True
        )
    
    def _cleanup_files(self):
        """Clean up old uploaded files"""
        try:
            max_age = self.config.get('MAX_FILE_AGE_HOURS', 24)
            stats = self.file_storage.cleanup_old_files(max_age)
            
            if stats['uploads_cleaned'] > 0 or stats['temp_cleaned'] > 0:
                logger.info(f"File cleanup completed: {stats}")
        except Exception as e:
            logger.error(f"File cleanup failed: {e}")
    
    def _cleanup_jobs(self):
        """Clean up old job entries"""
        try:
            max_age = self.config.get('MAX_FILE_AGE_HOURS', 24)
            cleaned_count = self.job_tracker.cleanup_old_jobs(max_age)
            
            if cleaned_count > 0:
                logger.info(f"Job cleanup completed: {cleaned_count} jobs removed")
        except Exception as e:
            logger.error(f"Job cleanup failed: {e}")
    
    def _cleanup_temp_files(self):
        """Clean up temporary files more aggressively"""
        try:
            max_age = self.config.get('TEMP_FILE_AGE_HOURS', 2)
            stats = self.file_storage.cleanup_old_files(max_age)
            
            if stats['temp_cleaned'] > 0:
                logger.info(f"Temp file cleanup completed: {stats['temp_cleaned']} files removed")
        except Exception as e:
            logger.error(f"Temp file cleanup failed: {e}")
    
    def start(self):
        """Start the cleanup scheduler"""
        if self.config.get('AUTO_CLEANUP_ENABLED', True):
            self.scheduler.start()
            logger.info("File cleanup scheduler started")
        else:
            logger.info("Auto cleanup is disabled")
    
    def stop(self):
        """Stop the cleanup scheduler"""
        self.scheduler.stop()
        logger.info("File cleanup scheduler stopped")
    
    def run_manual_cleanup(self, max_age_hours: Optional[int] = None):
        """
        Run manual cleanup
        
        Args:
            max_age_hours: Override default max age
        """
        max_age = max_age_hours or self.config.get('MAX_FILE_AGE_HOURS', 24)
        
        try:
            # Clean files
            file_stats = self.file_storage.cleanup_old_files(max_age)
            
            # Clean jobs
            job_count = self.job_tracker.cleanup_old_jobs(max_age)
            
            results = {
                'files_cleaned': file_stats['uploads_cleaned'] + file_stats['temp_cleaned'],
                'jobs_cleaned': job_count,
                'max_age_hours': max_age
            }
            
            logger.info(f"Manual cleanup completed: {results}")
            return results
            
        except Exception as e:
            logger.error(f"Manual cleanup failed: {e}")
            raise

def create_cleanup_scheduler(file_storage_manager, job_tracker, config):
    """
    Factory function to create and configure cleanup scheduler
    
    Args:
        file_storage_manager: FileStorageManager instance
        job_tracker: JobTracker instance
        config: Application configuration
        
    Returns:
        FileCleanupScheduler instance
    """
    scheduler = FileCleanupScheduler(file_storage_manager, job_tracker, config)
    return scheduler
