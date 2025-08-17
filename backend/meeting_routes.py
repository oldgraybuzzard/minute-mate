"""
Meeting routes for MinuteMate
Handles meeting history, dashboard, and management endpoints
"""

import logging
import os
from flask import Blueprint, request, jsonify, send_file
from flask_login import login_required, current_user
from meeting_service import MeetingService
from models import db, Meeting

logger = logging.getLogger(__name__)

# Create meeting blueprint
meeting_bp = Blueprint('meetings', __name__, url_prefix='/api/meetings')

def create_response(success, message, data=None):
    """Create standardized API response"""
    response = {
        'success': success,
        'message': message
    }
    if data is not None:
        response['data'] = data
    return response

@meeting_bp.route('/', methods=['GET'])
@login_required
def get_meetings():
    """Get user's meetings with pagination and filtering"""
    try:
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)  # Max 100 per page
        search = request.args.get('search', '').strip()
        status = request.args.get('status', 'all')
        
        # Get meetings
        result = MeetingService.get_user_meetings(
            user_id=current_user.id,
            page=page,
            per_page=per_page,
            search=search if search else None,
            status=status if status != 'all' else None
        )
        
        return jsonify(create_response(True, "Meetings retrieved", result)), 200
        
    except Exception as e:
        logger.error(f"Get meetings endpoint error: {str(e)}")
        return jsonify(create_response(False, "Failed to get meetings")), 500

@meeting_bp.route('/<meeting_id>', methods=['GET'])
@login_required
def get_meeting(meeting_id):
    """Get a specific meeting by ID"""
    try:
        meeting = MeetingService.get_meeting_by_id(meeting_id, current_user.id)
        
        if not meeting:
            return jsonify(create_response(False, "Meeting not found")), 404
        
        return jsonify(create_response(
            True, 
            "Meeting retrieved", 
            {'meeting': meeting.to_dict()}
        )), 200
        
    except Exception as e:
        logger.error(f"Get meeting endpoint error: {str(e)}")
        return jsonify(create_response(False, "Failed to get meeting")), 500

@meeting_bp.route('/', methods=['POST'])
@login_required
def create_meeting():
    """Create a new meeting"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('title'):
            return jsonify(create_response(False, "Title is required")), 400
        
        # Create meeting
        success, result = MeetingService.create_meeting(
            user_id=current_user.id,
            title=data['title'],
            description=data.get('description'),
            meeting_date=data.get('meeting_date'),
            job_id=data.get('job_id')
        )
        
        if success:
            meeting = result
            return jsonify(create_response(
                True, 
                "Meeting created", 
                {'meeting': meeting.to_dict()}
            )), 201
        else:
            return jsonify(create_response(False, result)), 400
            
    except Exception as e:
        logger.error(f"Create meeting endpoint error: {str(e)}")
        return jsonify(create_response(False, "Failed to create meeting")), 500

@meeting_bp.route('/<meeting_id>', methods=['PUT'])
@login_required
def update_meeting(meeting_id):
    """Update a meeting"""
    try:
        data = request.get_json()
        
        # Update meeting
        success, result = MeetingService.update_meeting(
            meeting_id=meeting_id,
            user_id=current_user.id,
            **data
        )
        
        if success:
            meeting = result
            return jsonify(create_response(
                True, 
                "Meeting updated", 
                {'meeting': meeting.to_dict()}
            )), 200
        else:
            return jsonify(create_response(False, result)), 400
            
    except Exception as e:
        logger.error(f"Update meeting endpoint error: {str(e)}")
        return jsonify(create_response(False, "Failed to update meeting")), 500

@meeting_bp.route('/<meeting_id>', methods=['DELETE'])
@login_required
def delete_meeting(meeting_id):
    """Delete a meeting"""
    try:
        success, message = MeetingService.delete_meeting(meeting_id, current_user.id)
        
        if success:
            return jsonify(create_response(True, message)), 200
        else:
            return jsonify(create_response(False, message)), 400
            
    except Exception as e:
        logger.error(f"Delete meeting endpoint error: {str(e)}")
        return jsonify(create_response(False, "Failed to delete meeting")), 500

@meeting_bp.route('/dashboard', methods=['GET'])
@login_required
def get_dashboard():
    """Get dashboard data for the user"""
    try:
        # Get statistics
        stats = MeetingService.get_user_statistics(current_user.id)
        
        # Get recent meetings
        recent_meetings = MeetingService.get_recent_meetings(current_user.id, limit=5)
        
        dashboard_data = {
            'user': current_user.to_dict(),
            'statistics': stats,
            'recent_meetings': recent_meetings
        }
        
        return jsonify(create_response(
            True, 
            "Dashboard data retrieved", 
            dashboard_data
        )), 200
        
    except Exception as e:
        logger.error(f"Dashboard endpoint error: {str(e)}")
        return jsonify(create_response(False, "Failed to get dashboard data")), 500

@meeting_bp.route('/search', methods=['GET'])
@login_required
def search_meetings():
    """Search meetings"""
    try:
        query = request.args.get('q', '').strip()
        limit = min(request.args.get('limit', 10, type=int), 50)  # Max 50 results
        
        if not query:
            return jsonify(create_response(False, "Search query is required")), 400
        
        meetings = MeetingService.search_meetings(current_user.id, query, limit)
        
        return jsonify(create_response(
            True, 
            f"Found {len(meetings)} meetings", 
            {'meetings': meetings}
        )), 200
        
    except Exception as e:
        logger.error(f"Search meetings endpoint error: {str(e)}")
        return jsonify(create_response(False, "Search failed")), 500

@meeting_bp.route('/stats', methods=['GET'])
@login_required
def get_statistics():
    """Get detailed statistics for the user"""
    try:
        stats = MeetingService.get_user_statistics(current_user.id)
        
        return jsonify(create_response(
            True, 
            "Statistics retrieved", 
            {'statistics': stats}
        )), 200
        
    except Exception as e:
        logger.error(f"Statistics endpoint error: {str(e)}")
        return jsonify(create_response(False, "Failed to get statistics")), 500

@meeting_bp.route('/recent', methods=['GET'])
@login_required
def get_recent():
    """Get recent meetings"""
    try:
        limit = min(request.args.get('limit', 10, type=int), 20)  # Max 20 results
        meetings = MeetingService.get_recent_meetings(current_user.id, limit)
        
        return jsonify(create_response(
            True, 
            "Recent meetings retrieved", 
            {'meetings': meetings}
        )), 200
        
    except Exception as e:
        logger.error(f"Recent meetings endpoint error: {str(e)}")
        return jsonify(create_response(False, "Failed to get recent meetings")), 500

@meeting_bp.route('/list', methods=['GET'])
@login_required
def get_meetings_list():
    """Get paginated and filtered list of meetings for the user"""
    try:
        from sqlalchemy import or_, and_, desc, asc
        from datetime import datetime, timedelta

        # Get query parameters
        page = int(request.args.get('page', 1))
        limit = min(int(request.args.get('limit', 10)), 50)  # Max 50 items per page
        search = request.args.get('search', '').strip()
        status_filter = request.args.get('status', '').strip()
        date_range = request.args.get('date_range', '').strip()
        sort_by = request.args.get('sort_by', 'created_at_desc')

        # Build base query
        query = Meeting.query.filter_by(user_id=current_user.id)

        # Apply search filter
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Meeting.title.ilike(search_term),
                    Meeting.transcript.ilike(search_term),
                    Meeting.summary.ilike(search_term)
                )
            )

        # Apply status filter
        if status_filter:
            query = query.filter(Meeting.status == status_filter)

        # Apply date range filter
        if date_range:
            now = datetime.utcnow()
            if date_range == 'today':
                start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
                query = query.filter(Meeting.created_at >= start_date)
            elif date_range == 'week':
                start_date = now - timedelta(days=7)
                query = query.filter(Meeting.created_at >= start_date)
            elif date_range == 'month':
                start_date = now - timedelta(days=30)
                query = query.filter(Meeting.created_at >= start_date)
            elif date_range == 'quarter':
                start_date = now - timedelta(days=90)
                query = query.filter(Meeting.created_at >= start_date)
            elif date_range == 'year':
                start_date = now - timedelta(days=365)
                query = query.filter(Meeting.created_at >= start_date)

        # Apply sorting
        if sort_by == 'created_at_desc':
            query = query.order_by(desc(Meeting.created_at))
        elif sort_by == 'created_at_asc':
            query = query.order_by(asc(Meeting.created_at))
        elif sort_by == 'title_asc':
            query = query.order_by(asc(Meeting.title))
        elif sort_by == 'title_desc':
            query = query.order_by(desc(Meeting.title))
        elif sort_by == 'duration_desc':
            query = query.order_by(desc(Meeting.duration_minutes))
        elif sort_by == 'duration_asc':
            query = query.order_by(asc(Meeting.duration_minutes))
        else:
            query = query.order_by(desc(Meeting.created_at))

        # Get total count before pagination
        total_count = query.count()

        # Apply pagination
        offset = (page - 1) * limit
        meetings = query.offset(offset).limit(limit).all()

        # Format meeting data
        meetings_data = []
        for meeting in meetings:
            # Calculate attendees count from transcript if available
            attendees_count = None
            if meeting.transcript:
                # Simple heuristic: count unique speaker patterns
                import re
                speakers = set(re.findall(r'^([A-Z][a-z]+ [A-Z][a-z]+):', meeting.transcript, re.MULTILINE))
                attendees_count = len(speakers) if speakers else None

            # Format duration for display
            duration_display = None
            if meeting.duration_minutes:
                if meeting.duration_minutes >= 60:
                    hours = meeting.duration_minutes // 60
                    minutes = meeting.duration_minutes % 60
                    duration_display = f"{hours}h {minutes}m" if minutes > 0 else f"{hours}h"
                else:
                    duration_display = f"{meeting.duration_minutes}m"

            meetings_data.append({
                'id': meeting.id,
                'title': meeting.title,
                'status': meeting.status,
                'created_at': meeting.created_at.isoformat(),
                'updated_at': meeting.updated_at.isoformat(),
                'duration': duration_display,
                'duration_minutes': meeting.duration_minutes,
                'attendees_count': attendees_count,
                'has_transcript': bool(meeting.transcript),
                'has_summary': bool(meeting.action_items or meeting.key_decisions),
                'has_document': bool(meeting.docx_file_path)
            })

        # Calculate pagination info
        total_pages = (total_count + limit - 1) // limit
        has_next = page < total_pages
        has_prev = page > 1

        pagination_info = {
            'page': page,
            'limit': limit,
            'total': total_count,
            'total_pages': total_pages,
            'has_next': has_next,
            'has_prev': has_prev,
            'filtered': total_count  # For now, same as total
        }

        return jsonify(create_response(
            True,
            "Meetings list retrieved",
            {
                'meetings': meetings_data,
                'pagination': pagination_info
            }
        )), 200

    except Exception as e:
        logger.error(f"Meetings list endpoint error: {str(e)}")
        return jsonify(create_response(False, "Failed to load meetings list")), 500

@meeting_bp.route('/<meeting_id>/download', methods=['GET'])
@login_required
def download_meeting(meeting_id):
    """Download meeting document"""
    try:
        meeting = Meeting.query.filter_by(id=meeting_id, user_id=current_user.id).first()

        if not meeting:
            return jsonify(create_response(False, "Meeting not found")), 404

        if not meeting.docx_file_path or not os.path.exists(meeting.docx_file_path):
            return jsonify(create_response(False, "Document not available")), 404

        return send_file(
            meeting.docx_file_path,
            as_attachment=True,
            download_name=f"meeting-{meeting.title or meeting.id}.docx",
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )

    except Exception as e:
        logger.error(f"Download meeting endpoint error: {str(e)}")
        return jsonify(create_response(False, "Failed to download meeting")), 500

# Error handlers for the meeting blueprint
@meeting_bp.errorhandler(400)
def bad_request(error):
    return jsonify(create_response(False, "Bad request")), 400

@meeting_bp.errorhandler(401)
def unauthorized(error):
    return jsonify(create_response(False, "Unauthorized")), 401

@meeting_bp.errorhandler(403)
def forbidden(error):
    return jsonify(create_response(False, "Forbidden")), 403

@meeting_bp.errorhandler(404)
def not_found(error):
    return jsonify(create_response(False, "Not found")), 404

@meeting_bp.errorhandler(500)
def internal_error(error):
    return jsonify(create_response(False, "Internal server error")), 500
