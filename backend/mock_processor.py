"""
MinuteMate Mock Processor
Simulates the AI processing pipeline for demonstration purposes.
"""

import time
import threading
import logging
from datetime import datetime
from pathlib import Path
import json
import os
from job_tracker import JobStatus

logger = logging.getLogger(__name__)

class MockProcessor:
    """Mock processor that simulates AI transcription and meeting minutes generation"""
    
    def __init__(self, job_tracker, file_storage_manager):
        """
        Initialize mock processor
        
        Args:
            job_tracker: JobTracker instance
            file_storage_manager: FileStorageManager instance
        """
        self.job_tracker = job_tracker
        self.file_storage_manager = file_storage_manager
        self.processing_threads = {}
        
    def start_processing(self, job_id: str):
        """
        Start processing a job in a background thread
        
        Args:
            job_id: Job identifier
        """
        if job_id in self.processing_threads:
            logger.warning(f"Job {job_id} is already being processed")
            return
        
        thread = threading.Thread(target=self._process_job, args=(job_id,))
        thread.daemon = True
        self.processing_threads[job_id] = thread
        thread.start()
        
        logger.info(f"Started processing job {job_id}")
    
    def _process_job(self, job_id: str):
        """
        Process a job through all stages
        
        Args:
            job_id: Job identifier
        """
        try:
            job_info = self.job_tracker.get_job(job_id)
            if not job_info:
                logger.error(f"Job {job_id} not found")
                return
            
            logger.info(f"Processing job {job_id}: {job_info['filename']}")
            
            # Stage 1: Transcription
            self._simulate_transcription(job_id)
            
            # Stage 2: Parsing
            self._simulate_parsing(job_id)
            
            # Stage 3: Formatting
            self._simulate_formatting(job_id)
            
            # Stage 4: Export
            self._simulate_export(job_id)
            
            # Mark as completed
            self.job_tracker.update_job(
                job_id=job_id,
                status=JobStatus.COMPLETED,
                stage='completed',
                progress=100,
                message='Processing completed successfully!'
            )
            
            logger.info(f"Job {job_id} completed successfully")
            
        except Exception as e:
            logger.error(f"Job {job_id} failed: {str(e)}", exc_info=True)
            self.job_tracker.update_job(
                job_id=job_id,
                status=JobStatus.FAILED,
                stage='failed',
                progress=0,
                message=f'Processing failed: {str(e)}',
                error=str(e)
            )
        finally:
            # Clean up thread reference
            if job_id in self.processing_threads:
                del self.processing_threads[job_id]
    
    def _simulate_transcription(self, job_id: str):
        """Simulate AI transcription process"""
        logger.info(f"Starting transcription for job {job_id}")
        
        self.job_tracker.update_job(
            job_id=job_id,
            status=JobStatus.TRANSCRIBING,
            stage='transcribing',
            progress=10,
            message='Starting AI transcription...'
        )
        
        # Simulate transcription time
        for i in range(3):
            time.sleep(2)  # Simulate processing time
            progress = 10 + (i + 1) * 15
            self.job_tracker.update_job(
                job_id=job_id,
                progress=progress,
                message=f'Transcribing audio... {progress}%'
            )
        
        logger.info(f"Transcription completed for job {job_id}")
    
    def _simulate_parsing(self, job_id: str):
        """Simulate content parsing and analysis"""
        logger.info(f"Starting parsing for job {job_id}")
        
        self.job_tracker.update_job(
            job_id=job_id,
            stage='parsing',
            progress=55,
            message='Analyzing meeting content...'
        )
        
        # Simulate parsing time
        for i in range(2):
            time.sleep(1.5)
            progress = 55 + (i + 1) * 10
            self.job_tracker.update_job(
                job_id=job_id,
                progress=progress,
                message=f'Identifying speakers and motions... {progress}%'
            )
        
        logger.info(f"Parsing completed for job {job_id}")
    
    def _simulate_formatting(self, job_id: str):
        """Simulate meeting minutes formatting"""
        logger.info(f"Starting formatting for job {job_id}")
        
        self.job_tracker.update_job(
            job_id=job_id,
            stage='formatting',
            progress=75,
            message='Formatting meeting minutes...'
        )
        
        # Simulate formatting time
        for i in range(2):
            time.sleep(1)
            progress = 75 + (i + 1) * 10
            self.job_tracker.update_job(
                job_id=job_id,
                progress=progress,
                message=f'Creating professional format... {progress}%'
            )
        
        logger.info(f"Formatting completed for job {job_id}")
    
    def _simulate_export(self, job_id: str):
        """Simulate document export"""
        logger.info(f"Starting export for job {job_id}")
        
        self.job_tracker.update_job(
            job_id=job_id,
            stage='exporting',
            progress=95,
            message='Generating final document...'
        )
        
        # Create a mock result file
        job_info = self.job_tracker.get_job(job_id)
        output_dir = Path('output/documents')
        output_dir.mkdir(parents=True, exist_ok=True)

        result_filename = f"meeting_minutes_{job_id}.json"
        result_path = output_dir / result_filename

        # Create mock meeting minutes content
        mock_content = self._generate_mock_minutes(job_info)

        # Save as JSON for now (in real implementation, this would be DOCX)
        with open(result_path, 'w') as f:
            json.dump(mock_content, f, indent=2)

        logger.info(f"Created result file: {result_path}")

        # Update job with result file
        self.job_tracker.update_job(
            job_id=job_id,
            progress=100,
            message='Document generated successfully!',
            result_file=str(result_path)
        )
        
        time.sleep(0.5)  # Brief pause
        logger.info(f"Export completed for job {job_id}")
    
    def _generate_mock_minutes(self, job_info: dict) -> dict:
        """Generate mock meeting minutes content"""
        return {
            "meeting_title": "Meeting Minutes",
            "date": datetime.now().strftime("%B %d, %Y"),
            "time": datetime.now().strftime("%I:%M %p"),
            "filename": job_info.get('filename', 'Unknown'),
            "duration": "Approximately 5 minutes",
            "attendees": [
                "John Smith (Chair)",
                "Jane Doe (Secretary)",
                "Bob Johnson",
                "Alice Williams"
            ],
            "agenda_items": [
                {
                    "item": "Call to Order",
                    "time": "2:00 PM",
                    "discussion": "Meeting called to order by John Smith at 2:00 PM."
                },
                {
                    "item": "Review of Previous Minutes",
                    "time": "2:02 PM",
                    "discussion": "Previous meeting minutes were reviewed and approved unanimously."
                },
                {
                    "item": "Budget Discussion",
                    "time": "2:05 PM",
                    "discussion": "Team discussed the quarterly budget allocation and approved the proposed changes.",
                    "motion": "Motion to approve budget changes",
                    "seconded_by": "Jane Doe",
                    "result": "Approved unanimously"
                }
            ],
            "action_items": [
                {
                    "item": "Prepare quarterly report",
                    "assigned_to": "Jane Doe",
                    "due_date": "Next Friday"
                },
                {
                    "item": "Schedule follow-up meeting",
                    "assigned_to": "Bob Johnson",
                    "due_date": "End of week"
                }
            ],
            "adjournment": {
                "time": "2:30 PM",
                "motion_by": "Alice Williams"
            },
            "generated_by": "MinuteMate AI",
            "generated_at": datetime.now().isoformat()
        }

# Global mock processor instance
mock_processor = None

def get_mock_processor(job_tracker, file_storage_manager):
    """Get or create the global mock processor instance"""
    global mock_processor
    if mock_processor is None:
        mock_processor = MockProcessor(job_tracker, file_storage_manager)
    return mock_processor
