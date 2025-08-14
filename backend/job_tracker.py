"""
MinuteMate Job Tracker
Simple in-memory job tracking system for processing status.
In production, this would be replaced with a database or Redis.
"""

import threading
from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum

class JobStatus(Enum):
    """Job status enumeration"""
    UPLOADED = "uploaded"
    TRANSCRIBING = "transcribing"
    PARSING = "parsing"
    FORMATTING = "formatting"
    EXPORTING = "exporting"
    COMPLETED = "completed"
    FAILED = "failed"

class JobTracker:
    """Thread-safe job tracking system"""
    
    def __init__(self):
        self._jobs: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
    
    def create_job(self, job_id: str, filename: str, file_size: str,
                  file_path: Optional[str] = None, file_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a new job entry

        Args:
            job_id: Unique job identifier
            filename: Original filename
            file_size: Formatted file size string
            file_path: Path to uploaded file
            file_type: Type of file (audio/video)

        Returns:
            dict: Job information
        """
        with self._lock:
            job_info = {
                'job_id': job_id,
                'filename': filename,
                'file_size': file_size,
                'file_path': file_path,
                'file_type': file_type,
                'status': JobStatus.UPLOADED.value,
                'stage': 'uploaded',
                'progress': 0,
                'message': 'File uploaded successfully',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
                'error': None,
                'result_file': None
            }
            self._jobs[job_id] = job_info
            return job_info.copy()
    
    def update_job(self, job_id: str, status: Optional[JobStatus] = None, 
                   stage: Optional[str] = None, progress: Optional[int] = None,
                   message: Optional[str] = None, error: Optional[str] = None,
                   result_file: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Update job information
        
        Args:
            job_id: Job identifier
            status: New job status
            stage: Current processing stage
            progress: Progress percentage (0-100)
            message: Status message
            error: Error message if any
            result_file: Path to result file when completed
            
        Returns:
            dict: Updated job information or None if job not found
        """
        with self._lock:
            if job_id not in self._jobs:
                return None
            
            job = self._jobs[job_id]
            
            if status:
                job['status'] = status.value
            if stage:
                job['stage'] = stage
            if progress is not None:
                job['progress'] = progress
            if message:
                job['message'] = message
            if error:
                job['error'] = error
                job['status'] = JobStatus.FAILED.value
            if result_file:
                job['result_file'] = result_file
                
            job['updated_at'] = datetime.now().isoformat()
            
            return job.copy()
    
    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get job information
        
        Args:
            job_id: Job identifier
            
        Returns:
            dict: Job information or None if not found
        """
        with self._lock:
            job = self._jobs.get(job_id)
            return job.copy() if job else None
    
    def delete_job(self, job_id: str) -> bool:
        """
        Delete a job entry
        
        Args:
            job_id: Job identifier
            
        Returns:
            bool: True if job was deleted, False if not found
        """
        with self._lock:
            if job_id in self._jobs:
                del self._jobs[job_id]
                return True
            return False
    
    def get_all_jobs(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all jobs (for debugging/admin purposes)
        
        Returns:
            dict: All job information
        """
        with self._lock:
            return {job_id: job.copy() for job_id, job in self._jobs.items()}
    
    def cleanup_old_jobs(self, max_age_hours: int = 24) -> int:
        """
        Clean up jobs older than specified hours
        
        Args:
            max_age_hours: Maximum age in hours
            
        Returns:
            int: Number of jobs cleaned up
        """
        from datetime import timedelta
        
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        cleaned_count = 0
        
        with self._lock:
            jobs_to_delete = []
            for job_id, job in self._jobs.items():
                created_at = datetime.fromisoformat(job['created_at'])
                if created_at < cutoff_time:
                    jobs_to_delete.append(job_id)
            
            for job_id in jobs_to_delete:
                del self._jobs[job_id]
                cleaned_count += 1
        
        return cleaned_count

# Global job tracker instance
job_tracker = JobTracker()
