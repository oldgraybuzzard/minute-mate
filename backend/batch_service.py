"""
Batch processing service for MinuteMate
Handles batch upload and processing of multiple meeting recordings
"""

import logging
import uuid
import asyncio
import threading
from datetime import datetime, timezone
from typing import List, Dict, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from models import db, BatchJob, Meeting, User
from file_manager import FileStorageManager, FileValidator
from ai_processor import AIProcessor
from document_generator import DocumentGenerator
from template_service import TemplateService
import os
import zipfile
import tempfile

logger = logging.getLogger(__name__)

class BatchProcessor:
    """Handles batch processing of multiple meeting recordings"""
    
    def __init__(self):
        # Initialize with default paths
        base_upload_dir = os.path.join(os.path.dirname(__file__), '..', 'uploads')
        base_output_dir = os.path.join(os.path.dirname(__file__), '..', 'output')
        temp_dir = os.path.join(os.path.dirname(__file__), '..', 'temp')

        self.file_manager = FileStorageManager(base_upload_dir, base_output_dir, temp_dir)
        self.file_validator = FileValidator()
        self.ai_processor = AIProcessor()
        self.document_generator = DocumentGenerator(os.path.join(base_output_dir, 'documents'))
        self.template_service = TemplateService()
        self.max_workers = 3  # Limit concurrent processing
        self.active_batches = {}  # Track active batch jobs
        
    def create_batch_job(self, user_id: str, files: List[Dict], batch_config: Dict) -> Tuple[bool, any]:
        """Create a new batch processing job"""
        try:
            # Validate files
            validated_files = []
            total_size = 0
            
            for file_info in files:
                file_obj = file_info.get('file')
                filename = file_info.get('filename', file_obj.filename if file_obj else 'unknown')
                
                # Validate file
                is_valid, error_msg = self.file_validator.validate_file(file_obj, filename)
                if not is_valid:
                    logger.warning(f"Invalid file in batch: {filename} - {error_msg}")
                    continue
                
                file_size = self._get_file_size(file_obj)
                total_size += file_size
                
                validated_files.append({
                    'file': file_obj,
                    'filename': filename,
                    'size': file_size,
                    'status': 'pending'
                })
            
            if not validated_files:
                return False, "No valid files found in batch"
            
            # Check total size limit (500MB for batch)
            max_batch_size = 500 * 1024 * 1024  # 500MB
            if total_size > max_batch_size:
                return False, f"Batch size ({total_size / 1024 / 1024:.1f}MB) exceeds limit (500MB)"
            
            # Create batch job
            batch_job = BatchJob(
                user_id=user_id,
                name=batch_config.get('name', f'Batch Job {datetime.now().strftime("%Y-%m-%d %H:%M")}'),
                description=batch_config.get('description', ''),
                total_files=len(validated_files),
                template_id=batch_config.get('template_id'),
                processing_options=batch_config.get('processing_options', {}),
                status='created'
            )
            
            db.session.add(batch_job)
            db.session.commit()
            
            # Store files and create file entries
            batch_files = []
            for file_info in validated_files:
                try:
                    # Store file
                    file_path = self.file_manager.store_file(
                        file_info['file'], 
                        file_info['filename'],
                        user_id
                    )
                    
                    # Create batch file entry
                    batch_file = {
                        'id': str(uuid.uuid4()),
                        'batch_job_id': batch_job.id,
                        'filename': file_info['filename'],
                        'file_path': file_path,
                        'size': file_info['size'],
                        'status': 'uploaded',
                        'created_at': datetime.now(timezone.utc).isoformat()
                    }
                    
                    batch_files.append(batch_file)
                    
                except Exception as e:
                    logger.error(f"Failed to store file {file_info['filename']}: {str(e)}")
                    continue
            
            # Update batch job with file information
            batch_job.files_data = batch_files
            batch_job.uploaded_files = len(batch_files)
            batch_job.status = 'uploaded' if batch_files else 'failed'
            db.session.commit()
            
            logger.info(f"Batch job created: {batch_job.id} with {len(batch_files)} files")
            return True, batch_job
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Batch job creation error: {str(e)}")
            return False, str(e)
    
    def start_batch_processing(self, batch_job_id: str) -> Tuple[bool, str]:
        """Start processing a batch job"""
        try:
            batch_job = BatchJob.query.get(batch_job_id)
            if not batch_job:
                return False, "Batch job not found"
            
            if batch_job.status not in ['uploaded', 'paused']:
                return False, f"Cannot start batch in status: {batch_job.status}"
            
            # Update status
            batch_job.status = 'processing'
            batch_job.started_at = datetime.now(timezone.utc)
            db.session.commit()
            
            # Start processing in background thread
            thread = threading.Thread(
                target=self._process_batch_async,
                args=(batch_job_id,),
                daemon=True
            )
            thread.start()
            
            self.active_batches[batch_job_id] = {
                'thread': thread,
                'status': 'processing'
            }
            
            logger.info(f"Started batch processing: {batch_job_id}")
            return True, "Batch processing started"
            
        except Exception as e:
            logger.error(f"Batch start error: {str(e)}")
            return False, str(e)
    
    def _process_batch_async(self, batch_job_id: str):
        """Process batch job asynchronously"""
        try:
            batch_job = BatchJob.query.get(batch_job_id)
            if not batch_job:
                logger.error(f"Batch job not found: {batch_job_id}")
                return
            
            files_data = batch_job.files_data or []
            processed_count = 0
            failed_count = 0
            
            # Process files with limited concurrency
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit all file processing tasks
                future_to_file = {
                    executor.submit(self._process_batch_file, batch_job, file_data): file_data
                    for file_data in files_data
                    if file_data.get('status') == 'uploaded'
                }
                
                # Process completed tasks
                for future in as_completed(future_to_file):
                    file_data = future_to_file[future]
                    try:
                        success, result = future.result()
                        if success:
                            processed_count += 1
                            file_data['status'] = 'completed'
                            file_data['meeting_id'] = result.get('meeting_id')
                        else:
                            failed_count += 1
                            file_data['status'] = 'failed'
                            file_data['error'] = result
                        
                        # Update progress
                        batch_job.processed_files = processed_count
                        batch_job.failed_files = failed_count
                        batch_job.files_data = files_data
                        db.session.commit()
                        
                        logger.info(f"Batch {batch_job_id}: Processed {file_data['filename']} - {'Success' if success else 'Failed'}")
                        
                    except Exception as e:
                        logger.error(f"Batch file processing error: {str(e)}")
                        failed_count += 1
                        file_data['status'] = 'failed'
                        file_data['error'] = str(e)
            
            # Update final batch status
            batch_job.completed_at = datetime.now(timezone.utc)
            batch_job.processed_files = processed_count
            batch_job.failed_files = failed_count
            
            if failed_count == 0:
                batch_job.status = 'completed'
            elif processed_count == 0:
                batch_job.status = 'failed'
            else:
                batch_job.status = 'partial'
            
            db.session.commit()
            
            # Remove from active batches
            if batch_job_id in self.active_batches:
                del self.active_batches[batch_job_id]
            
            logger.info(f"Batch processing completed: {batch_job_id} - {processed_count} success, {failed_count} failed")
            
        except Exception as e:
            logger.error(f"Batch processing error: {str(e)}")
            # Update batch status to failed
            try:
                batch_job = BatchJob.query.get(batch_job_id)
                if batch_job:
                    batch_job.status = 'failed'
                    batch_job.error_message = str(e)
                    batch_job.completed_at = datetime.now(timezone.utc)
                    db.session.commit()
            except:
                pass
    
    def _process_batch_file(self, batch_job, file_data: Dict) -> Tuple[bool, any]:
        """Process a single file in a batch"""
        try:
            filename = file_data['filename']
            file_path = file_data['file_path']
            
            # Check if file exists
            if not os.path.exists(file_path):
                return False, "File not found"
            
            # Get template if specified
            template = None
            if batch_job.template_id:
                template = self.template_service.get_template(batch_job.template_id, batch_job.user_id)
            
            # Create meeting record
            meeting_title = self._extract_meeting_title(filename)
            meeting = Meeting(
                user_id=batch_job.user_id,
                title=meeting_title,
                file_path=file_path,
                original_filename=filename,
                template_id=batch_job.template_id,
                batch_job_id=batch_job.id,
                status='processing'
            )
            
            db.session.add(meeting)
            db.session.commit()
            
            # Process with AI (if available)
            processing_options = batch_job.processing_options or {}
            
            if self.ai_processor.is_available():
                # Transcribe audio
                transcript = self.ai_processor.transcribe_audio(file_path)
                if not transcript:
                    meeting.status = 'failed'
                    meeting.error_message = 'Transcription failed'
                    db.session.commit()
                    return False, "Transcription failed"
                
                meeting.transcript = transcript
                
                # Generate minutes if template is available
                if template:
                    minutes = self.ai_processor.generate_minutes(
                        transcript, 
                        template.get('content', {}),
                        processing_options
                    )
                    meeting.minutes = minutes
                
                # Generate documents
                if processing_options.get('generate_documents', True):
                    doc_formats = processing_options.get('document_formats', ['docx'])
                    for format_type in doc_formats:
                        try:
                            doc_path = self.document_generator.generate_document(
                                meeting.minutes or meeting.transcript,
                                format_type,
                                meeting.title,
                                template_name=template.get('name') if template else 'professional'
                            )
                            
                            if not meeting.document_paths:
                                meeting.document_paths = {}
                            meeting.document_paths[format_type] = doc_path
                            
                        except Exception as e:
                            logger.warning(f"Document generation failed for {format_type}: {str(e)}")
            
            # Update meeting status
            meeting.status = 'completed'
            meeting.processed_at = datetime.now(timezone.utc)
            db.session.commit()
            
            return True, {'meeting_id': meeting.id}
            
        except Exception as e:
            logger.error(f"Batch file processing error: {str(e)}")
            return False, str(e)
    
    def get_batch_status(self, batch_job_id: str, user_id: str) -> Tuple[bool, any]:
        """Get status of a batch job"""
        try:
            batch_job = BatchJob.query.filter_by(id=batch_job_id, user_id=user_id).first()
            if not batch_job:
                return False, "Batch job not found"
            
            return True, batch_job.to_dict()
            
        except Exception as e:
            logger.error(f"Get batch status error: {str(e)}")
            return False, str(e)
    
    def get_user_batches(self, user_id: str, limit: int = 50) -> List[Dict]:
        """Get all batch jobs for a user"""
        try:
            batches = BatchJob.query.filter_by(user_id=user_id)\
                                  .order_by(BatchJob.created_at.desc())\
                                  .limit(limit).all()
            
            return [batch.to_dict() for batch in batches]
            
        except Exception as e:
            logger.error(f"Get user batches error: {str(e)}")
            return []
    
    def cancel_batch(self, batch_job_id: str, user_id: str) -> Tuple[bool, str]:
        """Cancel a running batch job"""
        try:
            batch_job = BatchJob.query.filter_by(id=batch_job_id, user_id=user_id).first()
            if not batch_job:
                return False, "Batch job not found"
            
            if batch_job.status not in ['processing', 'uploaded']:
                return False, f"Cannot cancel batch in status: {batch_job.status}"
            
            # Update status
            batch_job.status = 'cancelled'
            batch_job.completed_at = datetime.now(timezone.utc)
            db.session.commit()
            
            # Remove from active batches (thread will finish naturally)
            if batch_job_id in self.active_batches:
                del self.active_batches[batch_job_id]
            
            logger.info(f"Batch cancelled: {batch_job_id}")
            return True, "Batch job cancelled"
            
        except Exception as e:
            logger.error(f"Cancel batch error: {str(e)}")
            return False, str(e)
    
    def create_batch_download(self, batch_job_id: str, user_id: str) -> Tuple[bool, any]:
        """Create a ZIP file with all batch results"""
        try:
            batch_job = BatchJob.query.filter_by(id=batch_job_id, user_id=user_id).first()
            if not batch_job:
                return False, "Batch job not found"
            
            if batch_job.status not in ['completed', 'partial']:
                return False, "Batch not ready for download"
            
            # Create temporary ZIP file
            temp_dir = tempfile.mkdtemp()
            zip_path = os.path.join(temp_dir, f"batch_{batch_job_id}.zip")
            
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Add batch summary
                summary = self._create_batch_summary(batch_job)
                zipf.writestr("batch_summary.txt", summary)
                
                # Add completed meeting files
                for file_data in batch_job.files_data or []:
                    if file_data.get('status') == 'completed' and file_data.get('meeting_id'):
                        meeting = Meeting.query.get(file_data['meeting_id'])
                        if meeting:
                            # Add transcript
                            if meeting.transcript:
                                transcript_name = f"{meeting.title}_transcript.txt"
                                zipf.writestr(transcript_name, meeting.transcript)
                            
                            # Add minutes
                            if meeting.minutes:
                                minutes_name = f"{meeting.title}_minutes.txt"
                                zipf.writestr(minutes_name, meeting.minutes)
                            
                            # Add generated documents
                            if meeting.document_paths:
                                for format_type, doc_path in meeting.document_paths.items():
                                    if os.path.exists(doc_path):
                                        doc_name = f"{meeting.title}.{format_type}"
                                        zipf.write(doc_path, doc_name)
            
            return True, zip_path
            
        except Exception as e:
            logger.error(f"Create batch download error: {str(e)}")
            return False, str(e)
    
    def _get_file_size(self, file_obj) -> int:
        """Get file size"""
        try:
            file_obj.seek(0, 2)  # Seek to end
            size = file_obj.tell()
            file_obj.seek(0)  # Reset to beginning
            return size
        except:
            return 0
    
    def _extract_meeting_title(self, filename: str) -> str:
        """Extract meeting title from filename"""
        # Remove extension and clean up
        title = os.path.splitext(filename)[0]
        title = title.replace('_', ' ').replace('-', ' ')
        return title.title()
    
    def _create_batch_summary(self, batch_job) -> str:
        """Create a summary text for the batch"""
        summary = f"""Batch Processing Summary
========================

Batch Name: {batch_job.name}
Description: {batch_job.description or 'No description'}
Created: {batch_job.created_at}
Started: {batch_job.started_at or 'Not started'}
Completed: {batch_job.completed_at or 'Not completed'}

Files Summary:
- Total Files: {batch_job.total_files}
- Uploaded: {batch_job.uploaded_files}
- Processed: {batch_job.processed_files}
- Failed: {batch_job.failed_files}

Status: {batch_job.status.upper()}

File Details:
"""
        
        for i, file_data in enumerate(batch_job.files_data or [], 1):
            summary += f"\n{i}. {file_data['filename']}"
            summary += f"\n   Status: {file_data.get('status', 'unknown').upper()}"
            if file_data.get('error'):
                summary += f"\n   Error: {file_data['error']}"
            summary += "\n"
        
        return summary

# Global batch processor instance
batch_processor = BatchProcessor()
