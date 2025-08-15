"""
Template routes for MinuteMate
Handles meeting template management endpoints
"""

import logging
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from template_service import TemplateService
from models import db, MeetingTemplate

logger = logging.getLogger(__name__)

# Create template blueprint
template_bp = Blueprint('templates', __name__, url_prefix='/api/templates')

def create_response(success, message, data=None):
    """Create standardized API response"""
    response = {
        'success': success,
        'message': message
    }
    if data is not None:
        response['data'] = data
    return response

@template_bp.route('/', methods=['GET'])
@login_required
def get_templates():
    """Get user's templates including public templates"""
    try:
        include_public = request.args.get('include_public', 'true').lower() == 'true'
        category = request.args.get('category')
        
        templates = TemplateService.get_user_templates(
            user_id=current_user.id,
            include_public=include_public
        )
        
        # Filter by category if specified
        if category and category != 'all':
            templates = [t for t in templates if t.get('category') == category]
        
        return jsonify(create_response(
            True, 
            f"Found {len(templates)} templates", 
            {'templates': templates}
        )), 200
        
    except Exception as e:
        logger.error(f"Get templates endpoint error: {str(e)}")
        return jsonify(create_response(False, "Failed to get templates")), 500

@template_bp.route('/<template_id>', methods=['GET'])
@login_required
def get_template(template_id):
    """Get a specific template by ID"""
    try:
        template = TemplateService.get_template_by_id(template_id, current_user.id)
        
        if not template:
            return jsonify(create_response(False, "Template not found")), 404
        
        return jsonify(create_response(
            True, 
            "Template retrieved", 
            {'template': template.to_dict()}
        )), 200
        
    except Exception as e:
        logger.error(f"Get template endpoint error: {str(e)}")
        return jsonify(create_response(False, "Failed to get template")), 500

@template_bp.route('/', methods=['POST'])
@login_required
def create_template():
    """Create a new template"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('name'):
            return jsonify(create_response(False, "Template name is required")), 400
        
        # Create template
        success, result = TemplateService.create_template(
            user_id=current_user.id,
            name=data['name'],
            description=data.get('description'),
            category=data.get('category', 'general'),
            sections=data.get('sections'),
            formatting_options=data.get('formatting_options'),
            is_public=data.get('is_public', False)
        )
        
        if success:
            template = result
            return jsonify(create_response(
                True, 
                "Template created", 
                {'template': template.to_dict()}
            )), 201
        else:
            return jsonify(create_response(False, result)), 400
            
    except Exception as e:
        logger.error(f"Create template endpoint error: {str(e)}")
        return jsonify(create_response(False, "Failed to create template")), 500

@template_bp.route('/<template_id>', methods=['PUT'])
@login_required
def update_template(template_id):
    """Update a template"""
    try:
        data = request.get_json()
        
        # Update template
        success, result = TemplateService.update_template(
            template_id=template_id,
            user_id=current_user.id,
            **data
        )
        
        if success:
            template = result
            return jsonify(create_response(
                True, 
                "Template updated", 
                {'template': template.to_dict()}
            )), 200
        else:
            return jsonify(create_response(False, result)), 400
            
    except Exception as e:
        logger.error(f"Update template endpoint error: {str(e)}")
        return jsonify(create_response(False, "Failed to update template")), 500

@template_bp.route('/<template_id>', methods=['DELETE'])
@login_required
def delete_template(template_id):
    """Delete a template"""
    try:
        success, message = TemplateService.delete_template(template_id, current_user.id)
        
        if success:
            return jsonify(create_response(True, message)), 200
        else:
            return jsonify(create_response(False, message)), 400
            
    except Exception as e:
        logger.error(f"Delete template endpoint error: {str(e)}")
        return jsonify(create_response(False, "Failed to delete template")), 500

@template_bp.route('/<template_id>/duplicate', methods=['POST'])
@login_required
def duplicate_template(template_id):
    """Duplicate a template"""
    try:
        data = request.get_json() or {}
        new_name = data.get('name')
        
        success, result = TemplateService.duplicate_template(
            template_id=template_id,
            user_id=current_user.id,
            new_name=new_name
        )
        
        if success:
            template = result
            return jsonify(create_response(
                True, 
                "Template duplicated", 
                {'template': template.to_dict()}
            )), 201
        else:
            return jsonify(create_response(False, result)), 400
            
    except Exception as e:
        logger.error(f"Duplicate template endpoint error: {str(e)}")
        return jsonify(create_response(False, "Failed to duplicate template")), 500

@template_bp.route('/defaults', methods=['POST'])
@login_required
def create_default_templates():
    """Create default templates for the user"""
    try:
        templates = TemplateService.create_default_templates(current_user.id)
        
        return jsonify(create_response(
            True, 
            f"Created {len(templates)} default templates", 
            {'templates': [t.to_dict() for t in templates]}
        )), 201
        
    except Exception as e:
        logger.error(f"Create default templates endpoint error: {str(e)}")
        return jsonify(create_response(False, "Failed to create default templates")), 500

@template_bp.route('/categories', methods=['GET'])
@login_required
def get_categories():
    """Get available template categories"""
    try:
        categories = [
            {'value': 'board', 'label': 'Board Meeting', 'description': 'Formal governance meetings'},
            {'value': 'governance', 'label': 'Governance & Parliamentary', 'description': 'Robert\'s Rules and formal parliamentary procedure'},
            {'value': 'team', 'label': 'Team Meeting', 'description': 'Team standups and check-ins'},
            {'value': 'project', 'label': 'Project Meeting', 'description': 'Project reviews and planning'},
            {'value': 'client', 'label': 'Client Meeting', 'description': 'External client meetings'},
            {'value': 'general', 'label': 'General', 'description': 'General purpose meetings'},
            {'value': 'training', 'label': 'Training', 'description': 'Training and educational sessions'},
            {'value': 'interview', 'label': 'Interview', 'description': 'Job interviews and assessments'},
            {'value': 'sales', 'label': 'Sales', 'description': 'Sales calls and presentations'}
        ]
        
        return jsonify(create_response(
            True, 
            "Categories retrieved", 
            {'categories': categories}
        )), 200
        
    except Exception as e:
        logger.error(f"Get categories endpoint error: {str(e)}")
        return jsonify(create_response(False, "Failed to get categories")), 500

@template_bp.route('/sections', methods=['GET'])
@login_required
def get_available_sections():
    """Get available template sections"""
    try:
        sections = {
            'header': {
                'name': 'Header Information',
                'description': 'Meeting title, date, attendees, duration',
                'options': ['include_date', 'include_attendees', 'include_duration', 'include_company_info', 'include_meeting_number', 'include_quorum_status', 'include_organization_name']
            },
            'call_to_order': {
                'name': 'Call to Order',
                'description': 'Formal opening of the meeting (Robert\'s Rules)',
                'options': ['include_time', 'include_presiding_officer', 'include_secretary']
            },
            'roll_call': {
                'name': 'Roll Call & Attendance',
                'description': 'Attendance tracking and quorum verification',
                'options': ['track_attendance', 'note_absences', 'quorum_verification', 'proxy_votes']
            },
            'minutes_approval': {
                'name': 'Minutes Approval',
                'description': 'Approval of previous meeting minutes',
                'options': ['previous_meeting_date', 'corrections_noted', 'approval_motion']
            },
            'reports': {
                'name': 'Reports',
                'description': 'Officer, committee, and financial reports',
                'options': ['officer_reports', 'committee_reports', 'financial_reports', 'special_reports']
            },
            'correspondence': {
                'name': 'Correspondence',
                'description': 'Letters and communications received',
                'options': ['letters_received', 'communications']
            },
            'old_business': {
                'name': 'Old Business',
                'description': 'Unfinished business from previous meetings',
                'options': ['unfinished_business', 'tabled_items', 'postponed_items']
            },
            'new_business': {
                'name': 'New Business',
                'description': 'New items and proposals for consideration',
                'options': ['new_items', 'proposals', 'nominations']
            },
            'agenda': {
                'name': 'Agenda Items',
                'description': 'Meeting agenda and topics discussed',
                'options': ['auto_extract', 'numbered', 'include_time_estimates']
            },
            'motions': {
                'name': 'Motions & Voting',
                'description': 'Formal motions and voting results with Robert\'s Rules support',
                'options': ['include_voting', 'include_seconders', 'include_vote_counts', 'roberts_rules_format', 'track_amendments', 'point_of_order', 'privileged_motions', 'subsidiary_motions', 'incidental_motions']
            },
            'parliamentary_procedure': {
                'name': 'Parliamentary Procedure',
                'description': 'Points of order, appeals, and procedural matters',
                'options': ['points_of_order', 'appeals', 'questions_of_privilege']
            },
            'action_items': {
                'name': 'Action Items',
                'description': 'Tasks and follow-up actions',
                'options': ['include_assignee', 'include_deadline', 'include_priority', 'include_status', 'follow_up_required', 'committee_assignments']
            },
            'announcements': {
                'name': 'Announcements',
                'description': 'General announcements and upcoming events',
                'options': ['general_announcements', 'upcoming_events']
            },
            'adjournment': {
                'name': 'Adjournment',
                'description': 'Formal closing of the meeting',
                'options': ['include_time', 'next_meeting_date', 'motion_to_adjourn', 'seconded_by']
            },
            'signatures': {
                'name': 'Signatures & Approval',
                'description': 'Official signatures and approval section',
                'options': ['secretary_signature', 'president_signature', 'approval_date']
            },
            'decisions': {
                'name': 'Key Decisions',
                'description': 'Important decisions made during the meeting',
                'options': ['include_rationale', 'include_impact', 'include_alternatives']
            },
            'risks_issues': {
                'name': 'Risks & Issues',
                'description': 'Identified risks and issues',
                'options': ['auto_extract', 'include_severity', 'include_mitigation']
            },
            'next_steps': {
                'name': 'Next Steps',
                'description': 'Planned next steps and follow-up',
                'options': ['auto_extract', 'include_timeline', 'include_dependencies']
            },
            'transcript': {
                'name': 'Transcript',
                'description': 'Full or summarized meeting transcript',
                'options': ['summary_only', 'include_timestamps', 'include_speaker_names']
            }
        }
        
        return jsonify(create_response(
            True, 
            "Sections retrieved", 
            {'sections': sections}
        )), 200
        
    except Exception as e:
        logger.error(f"Get sections endpoint error: {str(e)}")
        return jsonify(create_response(False, "Failed to get sections")), 500

# Error handlers for the template blueprint
@template_bp.errorhandler(400)
def bad_request(error):
    return jsonify(create_response(False, "Bad request")), 400

@template_bp.errorhandler(401)
def unauthorized(error):
    return jsonify(create_response(False, "Unauthorized")), 401

@template_bp.errorhandler(403)
def forbidden(error):
    return jsonify(create_response(False, "Forbidden")), 403

@template_bp.errorhandler(404)
def not_found(error):
    return jsonify(create_response(False, "Not found")), 404

@template_bp.errorhandler(500)
def internal_error(error):
    return jsonify(create_response(False, "Internal server error")), 500
