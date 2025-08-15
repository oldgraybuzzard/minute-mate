"""
Document comparison routes for MinuteMate
Handles uploading edited documents and learning user preferences
"""

import logging
import os
import json
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify, send_file
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from models import db, Meeting, UserPreference
from document_comparison_service import DocumentComparisonService
import uuid

logger = logging.getLogger(__name__)

# Create document comparison blueprint
doc_comparison_bp = Blueprint('doc_comparison', __name__, url_prefix='/api/documents')

# Initialize comparison service
comparison_service = DocumentComparisonService()

def create_response(success, message, data=None):
    """Create standardized API response"""
    response = {
        'success': success,
        'message': message
    }
    if data is not None:
        response['data'] = data
    return response

def allowed_file(filename):
    """Check if file extension is allowed"""
    ALLOWED_EXTENSIONS = {'docx', 'doc'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@doc_comparison_bp.route('/upload-edited/<meeting_id>', methods=['POST'])
@login_required
def upload_edited_document(meeting_id):
    """
    Upload an edited version of a meeting document for comparison
    """
    try:
        # Validate meeting exists and belongs to user
        meeting = Meeting.query.filter_by(id=meeting_id, user_id=current_user.id).first()
        if not meeting:
            return jsonify(create_response(False, "Meeting not found")), 404
        
        # Check if original document exists
        if not meeting.docx_file_path or not os.path.exists(meeting.docx_file_path):
            return jsonify(create_response(False, "Original document not found")), 400
        
        # Check if file was uploaded
        if 'file' not in request.files:
            return jsonify(create_response(False, "No file uploaded")), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify(create_response(False, "No file selected")), 400
        
        if not allowed_file(file.filename):
            return jsonify(create_response(False, "Invalid file type. Only DOCX files are allowed")), 400
        
        # Create uploads directory for edited documents
        upload_dir = os.path.join(os.path.dirname(__file__), '..', 'uploads', 'edited_documents')
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save uploaded file
        filename = secure_filename(file.filename)
        file_id = str(uuid.uuid4())
        saved_filename = f"{file_id}_{filename}"
        file_path = os.path.join(upload_dir, saved_filename)
        file.save(file_path)
        
        # Perform document comparison
        comparison_result = comparison_service.compare_documents(
            original_path=meeting.docx_file_path,
            edited_path=file_path,
            user_id=current_user.id,
            meeting_id=meeting_id
        )
        
        # Update meeting record
        meeting.edited_document_path = file_path
        meeting.comparison_data = json.dumps(comparison_result)
        meeting.preferences_learned = True
        meeting.updated_at = datetime.now(timezone.utc)
        
        db.session.commit()
        
        logger.info(f"Edited document uploaded and compared for meeting {meeting_id}")
        
        return jsonify(create_response(
            True,
            "Document uploaded and preferences learned successfully",
            {
                'meeting_id': meeting_id,
                'comparison_summary': {
                    'preferences_learned': len(comparison_result.get('learned_preferences', {})),
                    'confidence_score': comparison_result.get('preference_confidence', 0),
                    'content_changes': len(comparison_result.get('text_changes', {}).get('additions', [])),
                    'formatting_changes': len(comparison_result.get('formatting_changes', {}))
                }
            }
        )), 200
        
    except Exception as e:
        logger.error(f"Upload edited document error: {str(e)}")
        return jsonify(create_response(False, "Failed to upload and compare document")), 500

@doc_comparison_bp.route('/comparison/<meeting_id>', methods=['GET'])
@login_required
def get_comparison_results(meeting_id):
    """
    Get comparison results for a meeting
    """
    try:
        meeting = Meeting.query.filter_by(id=meeting_id, user_id=current_user.id).first()
        if not meeting:
            return jsonify(create_response(False, "Meeting not found")), 404
        
        if not meeting.comparison_data:
            return jsonify(create_response(False, "No comparison data available")), 404
        
        comparison_data = json.loads(meeting.comparison_data)
        
        return jsonify(create_response(
            True,
            "Comparison results retrieved successfully",
            {
                'meeting_id': meeting_id,
                'comparison_data': comparison_data,
                'has_edited_version': bool(meeting.edited_document_path),
                'preferences_learned': meeting.preferences_learned
            }
        )), 200
        
    except Exception as e:
        logger.error(f"Get comparison results error: {str(e)}")
        return jsonify(create_response(False, "Failed to retrieve comparison results")), 500

@doc_comparison_bp.route('/preferences', methods=['GET'])
@login_required
def get_user_preferences():
    """
    Get all learned preferences for the current user
    """
    try:
        preferences = comparison_service.get_user_preferences(current_user.id)
        
        # Organize preferences by category
        organized_prefs = {
            'formatting': {},
            'content': {},
            'structure': {},
            'general': {}
        }
        
        for pref_key, pref_data in preferences.items():
            category = pref_data.get('category', 'general')
            if category not in organized_prefs:
                organized_prefs[category] = {}
            organized_prefs[category][pref_key] = pref_data
        
        return jsonify(create_response(
            True,
            "User preferences retrieved successfully",
            {
                'preferences': organized_prefs,
                'total_preferences': len(preferences),
                'categories': list(organized_prefs.keys())
            }
        )), 200
        
    except Exception as e:
        logger.error(f"Get user preferences error: {str(e)}")
        return jsonify(create_response(False, "Failed to retrieve user preferences")), 500

@doc_comparison_bp.route('/preferences/<preference_key>', methods=['DELETE'])
@login_required
def delete_preference(preference_key):
    """
    Delete a specific learned preference
    """
    try:
        preference = UserPreference.query.filter_by(
            user_id=current_user.id,
            preference_key=preference_key
        ).first()
        
        if not preference:
            return jsonify(create_response(False, "Preference not found")), 404
        
        db.session.delete(preference)
        db.session.commit()
        
        logger.info(f"Deleted preference {preference_key} for user {current_user.id}")
        
        return jsonify(create_response(
            True,
            f"Preference '{preference_key}' deleted successfully"
        )), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Delete preference error: {str(e)}")
        return jsonify(create_response(False, "Failed to delete preference")), 500

@doc_comparison_bp.route('/preferences/reset', methods=['POST'])
@login_required
def reset_all_preferences():
    """
    Reset all learned preferences for the current user
    """
    try:
        UserPreference.query.filter_by(user_id=current_user.id).delete()
        db.session.commit()
        
        logger.info(f"Reset all preferences for user {current_user.id}")
        
        return jsonify(create_response(
            True,
            "All preferences reset successfully"
        )), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Reset preferences error: {str(e)}")
        return jsonify(create_response(False, "Failed to reset preferences")), 500

@doc_comparison_bp.route('/apply-preferences/<meeting_id>', methods=['POST'])
@login_required
def apply_preferences_to_document(meeting_id):
    """
    Apply learned preferences to a meeting document
    """
    try:
        meeting = Meeting.query.filter_by(id=meeting_id, user_id=current_user.id).first()
        if not meeting:
            return jsonify(create_response(False, "Meeting not found")), 404
        
        if not meeting.docx_file_path or not os.path.exists(meeting.docx_file_path):
            return jsonify(create_response(False, "Original document not found")), 400
        
        # Apply preferences to document
        personalized_path = comparison_service.apply_preferences_to_document(
            meeting.docx_file_path,
            current_user.id
        )
        
        return jsonify(create_response(
            True,
            "Preferences applied to document successfully",
            {
                'meeting_id': meeting_id,
                'personalized_document_available': personalized_path != meeting.docx_file_path,
                'download_url': f"/api/documents/download-personalized/{meeting_id}" if personalized_path != meeting.docx_file_path else None
            }
        )), 200
        
    except Exception as e:
        logger.error(f"Apply preferences error: {str(e)}")
        return jsonify(create_response(False, "Failed to apply preferences")), 500

@doc_comparison_bp.route('/download-personalized/<meeting_id>', methods=['GET'])
@login_required
def download_personalized_document(meeting_id):
    """
    Download personalized document with applied preferences
    """
    try:
        meeting = Meeting.query.filter_by(id=meeting_id, user_id=current_user.id).first()
        if not meeting:
            return jsonify(create_response(False, "Meeting not found")), 404
        
        if not meeting.docx_file_path:
            return jsonify(create_response(False, "Document not found")), 404
        
        # Generate personalized document path
        personalized_path = meeting.docx_file_path.replace('.docx', '_personalized.docx')
        
        if not os.path.exists(personalized_path):
            # Apply preferences if personalized version doesn't exist
            personalized_path = comparison_service.apply_preferences_to_document(
                meeting.docx_file_path,
                current_user.id
            )
        
        if not os.path.exists(personalized_path):
            return jsonify(create_response(False, "Personalized document not available")), 404
        
        # Generate download filename
        original_filename = meeting.original_filename or "meeting_minutes.docx"
        download_filename = original_filename.replace('.docx', '_personalized.docx')
        
        return send_file(
            personalized_path,
            as_attachment=True,
            download_name=download_filename,
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
        
    except Exception as e:
        logger.error(f"Download personalized document error: {str(e)}")
        return jsonify(create_response(False, "Failed to download personalized document")), 500

@doc_comparison_bp.route('/download-edited/<meeting_id>', methods=['GET'])
@login_required
def download_edited_document(meeting_id):
    """
    Download the edited document that was uploaded by the user
    """
    try:
        meeting = Meeting.query.filter_by(id=meeting_id, user_id=current_user.id).first()
        if not meeting:
            return jsonify(create_response(False, "Meeting not found")), 404
        
        if not meeting.edited_document_path or not os.path.exists(meeting.edited_document_path):
            return jsonify(create_response(False, "Edited document not found")), 404
        
        # Generate download filename
        original_filename = meeting.original_filename or "meeting_minutes.docx"
        download_filename = original_filename.replace('.docx', '_edited.docx')
        
        return send_file(
            meeting.edited_document_path,
            as_attachment=True,
            download_name=download_filename,
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
        
    except Exception as e:
        logger.error(f"Download edited document error: {str(e)}")
        return jsonify(create_response(False, "Failed to download edited document")), 500

# Error handlers for the document comparison blueprint
@doc_comparison_bp.errorhandler(400)
def bad_request(error):
    return jsonify(create_response(False, "Bad request")), 400

@doc_comparison_bp.errorhandler(401)
def unauthorized(error):
    return jsonify(create_response(False, "Unauthorized")), 401

@doc_comparison_bp.errorhandler(404)
def not_found(error):
    return jsonify(create_response(False, "Not found")), 404

@doc_comparison_bp.errorhandler(500)
def internal_error(error):
    return jsonify(create_response(False, "Internal server error")), 500
