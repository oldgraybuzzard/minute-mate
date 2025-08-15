"""
Calendar routes for MinuteMate
Handles calendar integration endpoints
"""

import logging
from datetime import datetime, timezone, timedelta
from flask import Blueprint, request, jsonify, redirect, url_for
from flask_login import login_required, current_user
from calendar_service import CalendarService
from models import db, CalendarIntegration, CalendarEvent

logger = logging.getLogger(__name__)

# Create calendar blueprint
calendar_bp = Blueprint('calendar', __name__, url_prefix='/api/calendar')

# Initialize calendar service
calendar_service = CalendarService()

def create_response(success, message, data=None):
    """Create standardized API response"""
    response = {
        'success': success,
        'message': message
    }
    if data is not None:
        response['data'] = data
    return response

@calendar_bp.route('/providers', methods=['GET'])
@login_required
def get_providers():
    """Get available calendar providers"""
    try:
        providers = calendar_service.get_available_providers()
        return jsonify(create_response(
            True, 
            "Providers retrieved", 
            {'providers': providers}
        )), 200
        
    except Exception as e:
        logger.error(f"Get providers endpoint error: {str(e)}")
        return jsonify(create_response(False, "Failed to get providers")), 500

@calendar_bp.route('/connect/<provider>', methods=['GET'])
@login_required
def connect_calendar(provider):
    """Initiate calendar connection"""
    try:
        redirect_uri = request.args.get('redirect_uri', request.url_root + 'api/calendar/callback')
        
        success, auth_url = calendar_service.get_authorization_url(
            provider, current_user.id, redirect_uri
        )
        
        if success:
            return jsonify(create_response(
                True, 
                "Authorization URL generated", 
                {'auth_url': auth_url}
            )), 200
        else:
            return jsonify(create_response(False, auth_url)), 400
            
    except Exception as e:
        logger.error(f"Connect calendar endpoint error: {str(e)}")
        return jsonify(create_response(False, "Failed to initiate connection")), 500

@calendar_bp.route('/callback', methods=['GET'])
def calendar_callback():
    """Handle OAuth callback from calendar providers"""
    try:
        code = request.args.get('code')
        state = request.args.get('state')  # Contains user_id
        error = request.args.get('error')
        
        if error:
            logger.error(f"Calendar OAuth error: {error}")
            return redirect(f"/frontend/calendar.html?error={error}")
        
        if not code or not state:
            return redirect("/frontend/calendar.html?error=missing_parameters")
        
        # Determine provider from referrer or session
        provider = request.args.get('provider', 'google')  # Default to google
        redirect_uri = request.url_root + 'api/calendar/callback'
        
        success, result = calendar_service.connect_calendar(
            provider, state, code, redirect_uri
        )
        
        if success:
            return redirect("/frontend/calendar.html?success=connected")
        else:
            return redirect(f"/frontend/calendar.html?error={result}")
            
    except Exception as e:
        logger.error(f"Calendar callback error: {str(e)}")
        return redirect("/frontend/calendar.html?error=callback_failed")

@calendar_bp.route('/integrations', methods=['GET'])
@login_required
def get_integrations():
    """Get user's calendar integrations"""
    try:
        integrations = calendar_service.get_user_integrations(current_user.id)
        return jsonify(create_response(
            True, 
            f"Found {len(integrations)} integrations", 
            {'integrations': integrations}
        )), 200
        
    except Exception as e:
        logger.error(f"Get integrations endpoint error: {str(e)}")
        return jsonify(create_response(False, "Failed to get integrations")), 500

@calendar_bp.route('/integrations/<integration_id>', methods=['DELETE'])
@login_required
def disconnect_calendar(integration_id):
    """Disconnect a calendar integration"""
    try:
        success, message = calendar_service.disconnect_calendar(integration_id, current_user.id)
        
        if success:
            return jsonify(create_response(True, message)), 200
        else:
            return jsonify(create_response(False, message)), 400
            
    except Exception as e:
        logger.error(f"Disconnect calendar endpoint error: {str(e)}")
        return jsonify(create_response(False, "Failed to disconnect calendar")), 500

@calendar_bp.route('/integrations/<integration_id>/sync', methods=['POST'])
@login_required
def sync_calendar(integration_id):
    """Sync events from a calendar integration"""
    try:
        data = request.get_json() or {}
        days_back = data.get('days_back', 30)
        days_forward = data.get('days_forward', 90)
        
        success, result = calendar_service.sync_calendar_events(
            integration_id, days_back, days_forward
        )
        
        if success:
            return jsonify(create_response(
                True, 
                "Calendar sync completed", 
                result
            )), 200
        else:
            return jsonify(create_response(False, result.get('error', 'Sync failed'))), 400
            
    except Exception as e:
        logger.error(f"Sync calendar endpoint error: {str(e)}")
        return jsonify(create_response(False, "Failed to sync calendar")), 500

@calendar_bp.route('/events', methods=['GET'])
@login_required
def get_events():
    """Get calendar events for the user"""
    try:
        # Get query parameters
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        start_date = None
        end_date = None
        
        if start_date_str:
            start_date = datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
        if end_date_str:
            end_date = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))
        
        events = calendar_service.get_calendar_events(current_user.id, start_date, end_date)
        
        return jsonify(create_response(
            True, 
            f"Found {len(events)} events", 
            {'events': events}
        )), 200
        
    except Exception as e:
        logger.error(f"Get events endpoint error: {str(e)}")
        return jsonify(create_response(False, "Failed to get events")), 500

@calendar_bp.route('/events/follow-up', methods=['POST'])
@login_required
def create_follow_up_event():
    """Create a follow-up calendar event from a meeting"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['meeting_id', 'title', 'start_time', 'end_time']
        for field in required_fields:
            if not data.get(field):
                return jsonify(create_response(False, f"{field} is required")), 400
        
        success, result = calendar_service.create_follow_up_event(
            current_user.id, 
            data['meeting_id'], 
            data
        )
        
        if success:
            event = result
            return jsonify(create_response(
                True, 
                "Follow-up event created", 
                {'event': event.to_dict()}
            )), 201
        else:
            return jsonify(create_response(False, result)), 400
            
    except Exception as e:
        logger.error(f"Create follow-up event endpoint error: {str(e)}")
        return jsonify(create_response(False, "Failed to create follow-up event")), 500

@calendar_bp.route('/events/upcoming', methods=['GET'])
@login_required
def get_upcoming_events():
    """Get upcoming calendar events"""
    try:
        days_ahead = request.args.get('days', 7, type=int)
        
        start_date = datetime.now(timezone.utc)
        end_date = start_date + timedelta(days=days_ahead)
        
        events = calendar_service.get_calendar_events(current_user.id, start_date, end_date)
        
        return jsonify(create_response(
            True, 
            f"Found {len(events)} upcoming events", 
            {'events': events}
        )), 200
        
    except Exception as e:
        logger.error(f"Get upcoming events endpoint error: {str(e)}")
        return jsonify(create_response(False, "Failed to get upcoming events")), 500

@calendar_bp.route('/events/unprocessed', methods=['GET'])
@login_required
def get_unprocessed_events():
    """Get calendar events that haven't been processed for minutes"""
    try:
        events = CalendarEvent.query.filter_by(
            user_id=current_user.id,
            is_processed=False
        ).filter(
            CalendarEvent.end_time <= datetime.now(timezone.utc)
        ).order_by(CalendarEvent.start_time.desc()).all()
        
        return jsonify(create_response(
            True, 
            f"Found {len(events)} unprocessed events", 
            {'events': [event.to_dict() for event in events]}
        )), 200
        
    except Exception as e:
        logger.error(f"Get unprocessed events endpoint error: {str(e)}")
        return jsonify(create_response(False, "Failed to get unprocessed events")), 500

@calendar_bp.route('/events/<event_id>/process', methods=['POST'])
@login_required
def mark_event_processed(event_id):
    """Mark a calendar event as processed"""
    try:
        event = CalendarEvent.query.filter_by(
            id=event_id,
            user_id=current_user.id
        ).first()
        
        if not event:
            return jsonify(create_response(False, "Event not found")), 404
        
        event.is_processed = True
        db.session.commit()
        
        return jsonify(create_response(
            True, 
            "Event marked as processed", 
            {'event': event.to_dict()}
        )), 200
        
    except Exception as e:
        logger.error(f"Mark event processed endpoint error: {str(e)}")
        return jsonify(create_response(False, "Failed to mark event as processed")), 500

@calendar_bp.route('/sync-all', methods=['POST'])
@login_required
def sync_all_calendars():
    """Sync all active calendar integrations for the user"""
    try:
        integrations = CalendarIntegration.query.filter_by(
            user_id=current_user.id,
            is_active=True,
            sync_enabled=True
        ).all()
        
        if not integrations:
            return jsonify(create_response(False, "No active calendar integrations found")), 400
        
        results = []
        for integration in integrations:
            success, result = calendar_service.sync_calendar_events(integration.id)
            results.append({
                'integration_id': integration.id,
                'provider': integration.provider,
                'success': success,
                'result': result
            })
        
        successful_syncs = sum(1 for r in results if r['success'])
        
        return jsonify(create_response(
            True, 
            f"Synced {successful_syncs}/{len(integrations)} calendars", 
            {'results': results}
        )), 200
        
    except Exception as e:
        logger.error(f"Sync all calendars endpoint error: {str(e)}")
        return jsonify(create_response(False, "Failed to sync calendars")), 500

# Error handlers for the calendar blueprint
@calendar_bp.errorhandler(400)
def bad_request(error):
    return jsonify(create_response(False, "Bad request")), 400

@calendar_bp.errorhandler(401)
def unauthorized(error):
    return jsonify(create_response(False, "Unauthorized")), 401

@calendar_bp.errorhandler(403)
def forbidden(error):
    return jsonify(create_response(False, "Forbidden")), 403

@calendar_bp.errorhandler(404)
def not_found(error):
    return jsonify(create_response(False, "Not found")), 404

@calendar_bp.errorhandler(500)
def internal_error(error):
    return jsonify(create_response(False, "Internal server error")), 500
