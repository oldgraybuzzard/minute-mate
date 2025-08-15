"""
Profile and settings routes for MinuteMate
Handles user profile management and application settings
"""

import logging
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from models import db, User
import re

logger = logging.getLogger(__name__)

# Create profile blueprint
profile_bp = Blueprint('profile', __name__, url_prefix='/api/profile')

def create_response(success, message, data=None):
    """Create standardized API response"""
    response = {
        'success': success,
        'message': message
    }
    if data is not None:
        response['data'] = data
    return response

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """Validate password strength"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"
    
    return True, "Password is valid"

@profile_bp.route('/', methods=['GET'])
@login_required
def get_profile():
    """Get current user's profile information"""
    try:
        user_data = current_user.to_dict()
        
        # Add additional profile statistics
        from models import Meeting, BatchJob, CalendarIntegration
        
        # Meeting statistics
        total_meetings = Meeting.query.filter_by(user_id=current_user.id).count()
        completed_meetings = Meeting.query.filter_by(user_id=current_user.id, status='completed').count()
        
        # Batch statistics
        total_batches = BatchJob.query.filter_by(user_id=current_user.id).count()
        
        # Calendar integrations
        calendar_integrations = CalendarIntegration.query.filter_by(user_id=current_user.id, is_active=True).count()
        
        user_data['statistics'] = {
            'total_meetings': total_meetings,
            'completed_meetings': completed_meetings,
            'total_batches': total_batches,
            'calendar_integrations': calendar_integrations,
            'success_rate': round((completed_meetings / total_meetings * 100) if total_meetings > 0 else 0, 1)
        }
        
        return jsonify(create_response(
            True, 
            "Profile retrieved successfully", 
            {'user': user_data}
        )), 200
        
    except Exception as e:
        logger.error(f"Get profile error: {str(e)}")
        return jsonify(create_response(False, "Failed to retrieve profile")), 500

@profile_bp.route('/', methods=['PUT'])
@login_required
def update_profile():
    """Update user profile information"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify(create_response(False, "No data provided")), 400
        
        # Validate and update allowed fields
        allowed_fields = ['first_name', 'last_name', 'email', 'timezone', 'theme', 'language']
        updated_fields = []
        
        for field in allowed_fields:
            if field in data:
                value = data[field].strip() if isinstance(data[field], str) else data[field]
                
                # Validate specific fields
                if field == 'email':
                    if not validate_email(value):
                        return jsonify(create_response(False, "Invalid email format")), 400
                    
                    # Check if email is already taken by another user
                    existing_user = User.query.filter(User.email == value, User.id != current_user.id).first()
                    if existing_user:
                        return jsonify(create_response(False, "Email already in use")), 400
                
                elif field in ['first_name', 'last_name']:
                    if not value or len(value) < 1:
                        return jsonify(create_response(False, f"{field.replace('_', ' ').title()} is required")), 400
                    if len(value) > 50:
                        return jsonify(create_response(False, f"{field.replace('_', ' ').title()} is too long")), 400
                
                elif field == 'timezone':
                    # Basic timezone validation (you might want to use pytz for more comprehensive validation)
                    if value and not isinstance(value, str):
                        return jsonify(create_response(False, "Invalid timezone format")), 400
                
                elif field == 'theme':
                    if value not in ['light', 'dark', 'auto']:
                        return jsonify(create_response(False, "Invalid theme option")), 400
                
                elif field == 'language':
                    if value not in ['en', 'es', 'fr', 'de', 'it', 'pt', 'ja', 'zh']:
                        return jsonify(create_response(False, "Unsupported language")), 400
                
                # Update the field
                setattr(current_user, field, value)
                updated_fields.append(field.replace('_', ' ').title())
        
        if not updated_fields:
            return jsonify(create_response(False, "No valid fields to update")), 400
        
        # Update timestamp
        current_user.updated_at = datetime.now(timezone.utc)
        
        db.session.commit()
        
        logger.info(f"Profile updated for user {current_user.id}: {', '.join(updated_fields)}")
        
        return jsonify(create_response(
            True, 
            f"Profile updated: {', '.join(updated_fields)}", 
            {'user': current_user.to_dict()}
        )), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Update profile error: {str(e)}")
        return jsonify(create_response(False, "Failed to update profile")), 500

@profile_bp.route('/password', methods=['PUT'])
@login_required
def change_password():
    """Change user password"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify(create_response(False, "No data provided")), 400
        
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        confirm_password = data.get('confirm_password')
        
        if not all([current_password, new_password, confirm_password]):
            return jsonify(create_response(False, "All password fields are required")), 400
        
        # Verify current password
        if not check_password_hash(current_user.password_hash, current_password):
            return jsonify(create_response(False, "Current password is incorrect")), 400
        
        # Validate new password
        is_valid, message = validate_password(new_password)
        if not is_valid:
            return jsonify(create_response(False, message)), 400
        
        # Check password confirmation
        if new_password != confirm_password:
            return jsonify(create_response(False, "New passwords do not match")), 400
        
        # Check if new password is different from current
        if check_password_hash(current_user.password_hash, new_password):
            return jsonify(create_response(False, "New password must be different from current password")), 400
        
        # Update password
        current_user.password_hash = generate_password_hash(new_password)
        current_user.updated_at = datetime.now(timezone.utc)
        
        db.session.commit()
        
        logger.info(f"Password changed for user {current_user.id}")
        
        return jsonify(create_response(True, "Password changed successfully")), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Change password error: {str(e)}")
        return jsonify(create_response(False, "Failed to change password")), 500

@profile_bp.route('/preferences', methods=['GET'])
@login_required
def get_preferences():
    """Get user preferences and settings"""
    try:
        preferences = {
            'theme': current_user.theme or 'light',
            'timezone': current_user.timezone or 'UTC',
            'language': current_user.language or 'en',
            'notifications': {
                'email_notifications': True,  # Default values - you can add these fields to User model
                'processing_complete': True,
                'batch_complete': True,
                'calendar_sync': True
            },
            'processing': {
                'auto_generate_documents': True,
                'default_document_format': 'docx',
                'auto_start_batch': False,
                'max_file_size': 100,  # MB
                'default_template': None
            },
            'privacy': {
                'data_retention_days': 365,
                'share_analytics': False,
                'auto_delete_temp_files': True
            }
        }
        
        return jsonify(create_response(
            True, 
            "Preferences retrieved successfully", 
            {'preferences': preferences}
        )), 200
        
    except Exception as e:
        logger.error(f"Get preferences error: {str(e)}")
        return jsonify(create_response(False, "Failed to retrieve preferences")), 500

@profile_bp.route('/preferences', methods=['PUT'])
@login_required
def update_preferences():
    """Update user preferences and settings"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify(create_response(False, "No data provided")), 400
        
        # For now, we'll store basic preferences in the user model
        # In a production app, you might want a separate UserPreferences table
        
        updated_settings = []
        
        if 'theme' in data:
            if data['theme'] in ['light', 'dark', 'auto']:
                current_user.theme = data['theme']
                updated_settings.append('theme')
        
        if 'timezone' in data:
            current_user.timezone = data['timezone']
            updated_settings.append('timezone')
        
        if 'language' in data:
            if data['language'] in ['en', 'es', 'fr', 'de', 'it', 'pt', 'ja', 'zh']:
                current_user.language = data['language']
                updated_settings.append('language')
        
        # For other preferences, you would typically store them in a JSON field
        # or separate preferences table. For now, we'll just acknowledge them.
        
        if updated_settings:
            current_user.updated_at = datetime.now(timezone.utc)
            db.session.commit()
            
            logger.info(f"Preferences updated for user {current_user.id}: {', '.join(updated_settings)}")
        
        return jsonify(create_response(
            True, 
            "Preferences updated successfully", 
            {'updated_settings': updated_settings}
        )), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Update preferences error: {str(e)}")
        return jsonify(create_response(False, "Failed to update preferences")), 500

@profile_bp.route('/delete', methods=['DELETE'])
@login_required
def delete_account():
    """Delete user account and all associated data"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify(create_response(False, "No data provided")), 400
        
        password = data.get('password')
        confirmation = data.get('confirmation')
        
        if not password:
            return jsonify(create_response(False, "Password is required")), 400
        
        if confirmation != "DELETE":
            return jsonify(create_response(False, "Please type 'DELETE' to confirm")), 400
        
        # Verify password
        if not check_password_hash(current_user.password_hash, password):
            return jsonify(create_response(False, "Password is incorrect")), 400
        
        user_id = current_user.id
        
        # Delete associated data
        from models import Meeting, BatchJob, CalendarIntegration, CalendarEvent, MeetingTemplate
        
        # Delete calendar events
        CalendarEvent.query.filter_by(user_id=user_id).delete()
        
        # Delete calendar integrations
        CalendarIntegration.query.filter_by(user_id=user_id).delete()
        
        # Delete batch jobs
        BatchJob.query.filter_by(user_id=user_id).delete()
        
        # Delete meetings
        Meeting.query.filter_by(user_id=user_id).delete()
        
        # Delete templates
        MeetingTemplate.query.filter_by(user_id=user_id).delete()
        
        # Delete user account
        db.session.delete(current_user)
        db.session.commit()
        
        logger.info(f"Account deleted for user {user_id}")
        
        return jsonify(create_response(True, "Account deleted successfully")), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Delete account error: {str(e)}")
        return jsonify(create_response(False, "Failed to delete account")), 500

@profile_bp.route('/export', methods=['GET'])
@login_required
def export_data():
    """Export user data for download"""
    try:
        from models import Meeting, BatchJob, CalendarIntegration, MeetingTemplate
        import json
        
        # Collect user data
        user_data = {
            'profile': current_user.to_dict(),
            'meetings': [meeting.to_dict() for meeting in Meeting.query.filter_by(user_id=current_user.id).all()],
            'templates': [template.to_dict() for template in MeetingTemplate.query.filter_by(user_id=current_user.id).all()],
            'batch_jobs': [batch.to_dict() for batch in BatchJob.query.filter_by(user_id=current_user.id).all()],
            'calendar_integrations': [integration.to_dict() for integration in CalendarIntegration.query.filter_by(user_id=current_user.id).all()],
            'export_date': datetime.now(timezone.utc).isoformat()
        }
        
        return jsonify(create_response(
            True, 
            "Data exported successfully", 
            {'export_data': user_data}
        )), 200
        
    except Exception as e:
        logger.error(f"Export data error: {str(e)}")
        return jsonify(create_response(False, "Failed to export data")), 500

# Error handlers for the profile blueprint
@profile_bp.errorhandler(400)
def bad_request(error):
    return jsonify(create_response(False, "Bad request")), 400

@profile_bp.errorhandler(401)
def unauthorized(error):
    return jsonify(create_response(False, "Unauthorized")), 401

@profile_bp.errorhandler(403)
def forbidden(error):
    return jsonify(create_response(False, "Forbidden")), 403

@profile_bp.errorhandler(404)
def not_found(error):
    return jsonify(create_response(False, "Not found")), 404

@profile_bp.errorhandler(500)
def internal_error(error):
    return jsonify(create_response(False, "Internal server error")), 500
