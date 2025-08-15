"""
Batch processing routes for MinuteMate
Handles batch upload and processing endpoints
"""

import logging
import os
from flask import Blueprint, request, jsonify, send_file
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from batch_service import batch_processor
from models import db, BatchJob

logger = logging.getLogger(__name__)

# Create batch blueprint
batch_bp = Blueprint('batch', __name__, url_prefix='/api/batch')

def create_response(success, message, data=None):
    """Create standardized API response"""
    response = {
        'success': success,
        'message': message
    }
    if data is not None:
        response['data'] = data
    return response

@batch_bp.route('/upload', methods=['POST'])
@login_required
def upload_batch():
    """Upload multiple files for batch processing"""
    try:
        # Check if files are present
        if 'files' not in request.files:
            return jsonify(create_response(False, "No files provided")), 400
        
        files = request.files.getlist('files')
        if not files or all(f.filename == '' for f in files):
            return jsonify(create_response(False, "No files selected")), 400
        
        # Get batch configuration
        batch_config = {
            'name': request.form.get('batch_name', ''),
            'description': request.form.get('batch_description', ''),
            'template_id': request.form.get('template_id'),
            'processing_options': {
                'generate_documents': request.form.get('generate_documents', 'true').lower() == 'true',
                'document_formats': request.form.getlist('document_formats') or ['docx'],
                'auto_start': request.form.get('auto_start', 'false').lower() == 'true'
            }
        }
        
        # Prepare file list
        file_list = []
        for file in files:
            if file and file.filename:
                file_list.append({
                    'file': file,
                    'filename': secure_filename(file.filename)
                })
        
        if not file_list:
            return jsonify(create_response(False, "No valid files found")), 400
        
        # Create batch job
        success, result = batch_processor.create_batch_job(
            current_user.id, 
            file_list, 
            batch_config
        )
        
        if not success:
            return jsonify(create_response(False, result)), 400
        
        batch_job = result
        
        # Auto-start if requested
        if batch_config['processing_options'].get('auto_start', False):
            start_success, start_message = batch_processor.start_batch_processing(batch_job.id)
            if not start_success:
                logger.warning(f"Failed to auto-start batch {batch_job.id}: {start_message}")
        
        return jsonify(create_response(
            True, 
            f"Batch created with {len(file_list)} files", 
            {'batch_job': batch_job.to_dict()}
        )), 201
        
    except Exception as e:
        logger.error(f"Batch upload endpoint error: {str(e)}")
        return jsonify(create_response(False, "Failed to create batch job")), 500

@batch_bp.route('/<batch_id>/start', methods=['POST'])
@login_required
def start_batch(batch_id):
    """Start processing a batch job"""
    try:
        # Verify ownership
        batch_job = BatchJob.query.filter_by(id=batch_id, user_id=current_user.id).first()
        if not batch_job:
            return jsonify(create_response(False, "Batch job not found")), 404
        
        success, message = batch_processor.start_batch_processing(batch_id)
        
        if success:
            return jsonify(create_response(True, message)), 200
        else:
            return jsonify(create_response(False, message)), 400
            
    except Exception as e:
        logger.error(f"Start batch endpoint error: {str(e)}")
        return jsonify(create_response(False, "Failed to start batch processing")), 500

@batch_bp.route('/<batch_id>/cancel', methods=['POST'])
@login_required
def cancel_batch(batch_id):
    """Cancel a batch job"""
    try:
        success, message = batch_processor.cancel_batch(batch_id, current_user.id)
        
        if success:
            return jsonify(create_response(True, message)), 200
        else:
            return jsonify(create_response(False, message)), 400
            
    except Exception as e:
        logger.error(f"Cancel batch endpoint error: {str(e)}")
        return jsonify(create_response(False, "Failed to cancel batch job")), 500

@batch_bp.route('/<batch_id>/status', methods=['GET'])
@login_required
def get_batch_status(batch_id):
    """Get status of a batch job"""
    try:
        success, result = batch_processor.get_batch_status(batch_id, current_user.id)
        
        if success:
            return jsonify(create_response(
                True, 
                "Batch status retrieved", 
                {'batch_job': result}
            )), 200
        else:
            return jsonify(create_response(False, result)), 404
            
    except Exception as e:
        logger.error(f"Get batch status endpoint error: {str(e)}")
        return jsonify(create_response(False, "Failed to get batch status")), 500

@batch_bp.route('/', methods=['GET'])
@login_required
def list_batches():
    """List all batch jobs for the current user"""
    try:
        limit = request.args.get('limit', 50, type=int)
        status_filter = request.args.get('status')
        
        batches = batch_processor.get_user_batches(current_user.id, limit)
        
        # Filter by status if requested
        if status_filter:
            batches = [b for b in batches if b['status'] == status_filter]
        
        return jsonify(create_response(
            True, 
            f"Found {len(batches)} batch jobs", 
            {'batches': batches}
        )), 200
        
    except Exception as e:
        logger.error(f"List batches endpoint error: {str(e)}")
        return jsonify(create_response(False, "Failed to list batch jobs")), 500

@batch_bp.route('/<batch_id>/download', methods=['GET'])
@login_required
def download_batch_results(batch_id):
    """Download all results from a batch job as ZIP"""
    try:
        success, result = batch_processor.create_batch_download(batch_id, current_user.id)
        
        if not success:
            return jsonify(create_response(False, result)), 400
        
        zip_path = result
        
        # Send file and clean up
        def remove_file(response):
            try:
                os.remove(zip_path)
                os.rmdir(os.path.dirname(zip_path))
            except:
                pass
            return response
        
        return send_file(
            zip_path,
            as_attachment=True,
            download_name=f"batch_{batch_id}_results.zip",
            mimetype='application/zip'
        )
        
    except Exception as e:
        logger.error(f"Download batch endpoint error: {str(e)}")
        return jsonify(create_response(False, "Failed to create batch download")), 500

@batch_bp.route('/<batch_id>/retry', methods=['POST'])
@login_required
def retry_batch(batch_id):
    """Retry failed files in a batch job"""
    try:
        # Verify ownership
        batch_job = BatchJob.query.filter_by(id=batch_id, user_id=current_user.id).first()
        if not batch_job:
            return jsonify(create_response(False, "Batch job not found")), 404
        
        if batch_job.status not in ['failed', 'partial', 'completed']:
            return jsonify(create_response(False, "Cannot retry batch in current status")), 400
        
        # Reset failed files to uploaded status
        files_data = batch_job.files_data or []
        retry_count = 0
        
        for file_data in files_data:
            if file_data.get('status') == 'failed':
                file_data['status'] = 'uploaded'
                file_data.pop('error', None)
                retry_count += 1
        
        if retry_count == 0:
            return jsonify(create_response(False, "No failed files to retry")), 400
        
        # Update batch job
        batch_job.files_data = files_data
        batch_job.status = 'uploaded'
        batch_job.failed_files = max(0, batch_job.failed_files - retry_count)
        batch_job.error_message = None
        db.session.commit()
        
        # Start processing
        success, message = batch_processor.start_batch_processing(batch_id)
        
        if success:
            return jsonify(create_response(
                True, 
                f"Retrying {retry_count} failed files", 
                {'retry_count': retry_count}
            )), 200
        else:
            return jsonify(create_response(False, f"Failed to start retry: {message}")), 400
            
    except Exception as e:
        logger.error(f"Retry batch endpoint error: {str(e)}")
        return jsonify(create_response(False, "Failed to retry batch job")), 500

@batch_bp.route('/<batch_id>', methods=['DELETE'])
@login_required
def delete_batch(batch_id):
    """Delete a batch job and its associated data"""
    try:
        # Verify ownership
        batch_job = BatchJob.query.filter_by(id=batch_id, user_id=current_user.id).first()
        if not batch_job:
            return jsonify(create_response(False, "Batch job not found")), 404
        
        if batch_job.status == 'processing':
            return jsonify(create_response(False, "Cannot delete batch while processing")), 400
        
        # Delete associated meetings (optional - could be kept)
        # Meeting.query.filter_by(batch_job_id=batch_id).delete()
        
        # Delete batch job
        db.session.delete(batch_job)
        db.session.commit()
        
        logger.info(f"Batch job deleted: {batch_id}")
        return jsonify(create_response(True, "Batch job deleted successfully")), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Delete batch endpoint error: {str(e)}")
        return jsonify(create_response(False, "Failed to delete batch job")), 500

@batch_bp.route('/stats', methods=['GET'])
@login_required
def get_batch_stats():
    """Get batch processing statistics for the user"""
    try:
        # Get user's batch statistics
        batches = BatchJob.query.filter_by(user_id=current_user.id).all()
        
        stats = {
            'total_batches': len(batches),
            'total_files_processed': sum(b.processed_files for b in batches),
            'total_files_failed': sum(b.failed_files for b in batches),
            'status_counts': {},
            'recent_batches': []
        }
        
        # Count by status
        for batch in batches:
            status = batch.status
            stats['status_counts'][status] = stats['status_counts'].get(status, 0) + 1
        
        # Get recent batches
        recent_batches = sorted(batches, key=lambda b: b.created_at, reverse=True)[:5]
        stats['recent_batches'] = [b.to_dict() for b in recent_batches]
        
        return jsonify(create_response(
            True, 
            "Batch statistics retrieved", 
            {'stats': stats}
        )), 200
        
    except Exception as e:
        logger.error(f"Get batch stats endpoint error: {str(e)}")
        return jsonify(create_response(False, "Failed to get batch statistics")), 500

# Error handlers for the batch blueprint
@batch_bp.errorhandler(400)
def bad_request(error):
    return jsonify(create_response(False, "Bad request")), 400

@batch_bp.errorhandler(401)
def unauthorized(error):
    return jsonify(create_response(False, "Unauthorized")), 401

@batch_bp.errorhandler(403)
def forbidden(error):
    return jsonify(create_response(False, "Forbidden")), 403

@batch_bp.errorhandler(404)
def not_found(error):
    return jsonify(create_response(False, "Not found")), 404

@batch_bp.errorhandler(413)
def payload_too_large(error):
    return jsonify(create_response(False, "Files too large")), 413

@batch_bp.errorhandler(500)
def internal_error(error):
    return jsonify(create_response(False, "Internal server error")), 500
