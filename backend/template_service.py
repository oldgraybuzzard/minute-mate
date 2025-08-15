"""
Template service for MinuteMate
Handles meeting template management, creation, and customization
"""

import logging
from datetime import datetime, timezone
from flask_login import current_user
from models import db, MeetingTemplate, User
from sqlalchemy import desc, or_
from typing import List, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

class TemplateService:
    """Service for handling meeting template operations"""
    
    # Default template configurations
    DEFAULT_TEMPLATES = {
        'board_meeting': {
            'name': 'Board Meeting (Robert\'s Rules)',
            'description': 'Formal board meeting template following Robert\'s Rules of Order',
            'category': 'board',
            'sections': {
                'header': {
                    'enabled': True,
                    'include_date': True,
                    'include_attendees': True,
                    'include_duration': True,
                    'include_meeting_number': True,
                    'include_quorum_status': True
                },
                'call_to_order': {
                    'enabled': True,
                    'include_time': True,
                    'include_presiding_officer': True
                },
                'roll_call': {
                    'enabled': True,
                    'track_attendance': True,
                    'note_absences': True,
                    'quorum_verification': True
                },
                'agenda': {
                    'enabled': True,
                    'auto_extract': True,
                    'numbered': True,
                    'roberts_rules_order': True
                },
                'minutes_approval': {
                    'enabled': True,
                    'previous_meeting_date': True,
                    'corrections_noted': True
                },
                'reports': {
                    'enabled': True,
                    'officer_reports': True,
                    'committee_reports': True,
                    'financial_reports': True
                },
                'old_business': {
                    'enabled': True,
                    'unfinished_business': True,
                    'tabled_items': True
                },
                'new_business': {
                    'enabled': True,
                    'new_items': True,
                    'proposals': True
                },
                'motions': {
                    'enabled': True,
                    'include_voting': True,
                    'include_seconders': True,
                    'include_vote_counts': True,
                    'roberts_rules_format': True,
                    'track_amendments': True,
                    'point_of_order': True
                },
                'action_items': {
                    'enabled': True,
                    'include_assignee': True,
                    'include_deadline': True,
                    'include_priority': True,
                    'follow_up_required': True
                },
                'decisions': {
                    'enabled': True,
                    'include_rationale': True,
                    'voting_results': True
                },
                'adjournment': {
                    'enabled': True,
                    'include_time': True,
                    'next_meeting_date': True,
                    'motion_to_adjourn': True
                },
                'transcript': {
                    'enabled': False,
                    'summary_only': True
                }
            },
            'formatting_options': {
                'style': 'formal',
                'font_family': 'Times New Roman',
                'font_size': 12,
                'line_spacing': 1.5,
                'include_signatures': True,
                'include_approval_section': True,
                'roberts_rules_formatting': True,
                'include_parliamentary_notes': True
            }
        },
        'team_standup': {
            'name': 'Team Standup',
            'description': 'Daily/weekly team standup meeting template',
            'category': 'team',
            'sections': {
                'header': {
                    'enabled': True,
                    'include_date': True,
                    'include_attendees': True,
                    'include_duration': False
                },
                'agenda': {
                    'enabled': False,
                    'auto_extract': False
                },
                'action_items': {
                    'enabled': True,
                    'include_assignee': True,
                    'include_deadline': False,
                    'include_priority': False
                },
                'decisions': {
                    'enabled': True,
                    'include_rationale': False
                },
                'blockers': {
                    'enabled': True,
                    'auto_extract': True
                },
                'transcript': {
                    'enabled': True,
                    'summary_only': True
                }
            },
            'formatting_options': {
                'style': 'casual',
                'font_family': 'Arial',
                'font_size': 11,
                'line_spacing': 1.2,
                'include_signatures': False,
                'bullet_style': 'bullet'
            }
        },
        'project_review': {
            'name': 'Project Review',
            'description': 'Project milestone and review meeting template',
            'category': 'project',
            'sections': {
                'header': {
                    'enabled': True,
                    'include_date': True,
                    'include_attendees': True,
                    'include_duration': True
                },
                'agenda': {
                    'enabled': True,
                    'auto_extract': True,
                    'numbered': True
                },
                'action_items': {
                    'enabled': True,
                    'include_assignee': True,
                    'include_deadline': True,
                    'include_priority': True
                },
                'decisions': {
                    'enabled': True,
                    'include_rationale': True
                },
                'risks_issues': {
                    'enabled': True,
                    'auto_extract': True
                },
                'next_steps': {
                    'enabled': True,
                    'auto_extract': True
                },
                'transcript': {
                    'enabled': False,
                    'summary_only': True
                }
            },
            'formatting_options': {
                'style': 'professional',
                'font_family': 'Calibri',
                'font_size': 11,
                'line_spacing': 1.3,
                'include_signatures': False,
                'include_status_section': True
            }
        },
        'client_meeting': {
            'name': 'Client Meeting',
            'description': 'External client meeting template',
            'category': 'client',
            'sections': {
                'header': {
                    'enabled': True,
                    'include_date': True,
                    'include_attendees': True,
                    'include_duration': True,
                    'include_company_info': True
                },
                'agenda': {
                    'enabled': True,
                    'auto_extract': True,
                    'numbered': True
                },
                'action_items': {
                    'enabled': True,
                    'include_assignee': True,
                    'include_deadline': True,
                    'include_priority': False
                },
                'decisions': {
                    'enabled': True,
                    'include_rationale': False
                },
                'follow_up': {
                    'enabled': True,
                    'auto_extract': True
                },
                'transcript': {
                    'enabled': False,
                    'summary_only': True
                }
            },
            'formatting_options': {
                'style': 'professional',
                'font_family': 'Arial',
                'font_size': 11,
                'line_spacing': 1.2,
                'include_signatures': False,
                'include_confidentiality': True
            }
        },
        'roberts_rules_meeting': {
            'name': 'Robert\'s Rules Meeting',
            'description': 'Comprehensive Robert\'s Rules template for formal parliamentary procedure',
            'category': 'governance',
            'sections': {
                'header': {
                    'enabled': True,
                    'include_date': True,
                    'include_attendees': True,
                    'include_duration': True,
                    'include_meeting_number': True,
                    'include_organization_name': True
                },
                'call_to_order': {
                    'enabled': True,
                    'include_time': True,
                    'include_presiding_officer': True,
                    'include_secretary': True
                },
                'roll_call': {
                    'enabled': True,
                    'track_attendance': True,
                    'note_absences': True,
                    'quorum_verification': True,
                    'proxy_votes': True
                },
                'minutes_approval': {
                    'enabled': True,
                    'previous_meeting_date': True,
                    'corrections_noted': True,
                    'approval_motion': True
                },
                'reports': {
                    'enabled': True,
                    'officer_reports': True,
                    'committee_reports': True,
                    'financial_reports': True,
                    'special_reports': True
                },
                'correspondence': {
                    'enabled': True,
                    'letters_received': True,
                    'communications': True
                },
                'old_business': {
                    'enabled': True,
                    'unfinished_business': True,
                    'tabled_items': True,
                    'postponed_items': True
                },
                'new_business': {
                    'enabled': True,
                    'new_items': True,
                    'proposals': True,
                    'nominations': True
                },
                'motions': {
                    'enabled': True,
                    'include_voting': True,
                    'include_seconders': True,
                    'include_vote_counts': True,
                    'roberts_rules_format': True,
                    'track_amendments': True,
                    'point_of_order': True,
                    'privileged_motions': True,
                    'subsidiary_motions': True,
                    'incidental_motions': True
                },
                'parliamentary_procedure': {
                    'enabled': True,
                    'points_of_order': True,
                    'appeals': True,
                    'questions_of_privilege': True
                },
                'action_items': {
                    'enabled': True,
                    'include_assignee': True,
                    'include_deadline': True,
                    'committee_assignments': True
                },
                'announcements': {
                    'enabled': True,
                    'general_announcements': True,
                    'upcoming_events': True
                },
                'adjournment': {
                    'enabled': True,
                    'include_time': True,
                    'next_meeting_date': True,
                    'motion_to_adjourn': True,
                    'seconded_by': True
                },
                'signatures': {
                    'enabled': True,
                    'secretary_signature': True,
                    'president_signature': True,
                    'approval_date': True
                },
                'transcript': {
                    'enabled': False,
                    'summary_only': True
                }
            },
            'formatting_options': {
                'style': 'formal',
                'font_family': 'Times New Roman',
                'font_size': 12,
                'line_spacing': 1.5,
                'include_signatures': True,
                'include_approval_section': True,
                'roberts_rules_formatting': True,
                'include_parliamentary_notes': True,
                'formal_language': True,
                'numbered_sections': True
            }
        }
    }
    
    @staticmethod
    def create_template(user_id: str, name: str, description: str = None, 
                       category: str = 'general', sections: dict = None, 
                       formatting_options: dict = None, is_public: bool = False) -> Tuple[bool, any]:
        """Create a new meeting template"""
        try:
            # Validate sections
            if not sections:
                sections = TemplateService._get_default_sections()
            
            # Validate formatting options
            if not formatting_options:
                formatting_options = TemplateService._get_default_formatting()
            
            template = MeetingTemplate(
                user_id=user_id,
                name=name,
                description=description,
                category=category,
                sections=sections,
                formatting_options=formatting_options,
                is_public=is_public
            )
            
            db.session.add(template)
            db.session.commit()
            
            logger.info(f"Template created: {template.name} for user {user_id}")
            return True, template
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Template creation error: {str(e)}")
            return False, "Failed to create template"
    
    @staticmethod
    def get_user_templates(user_id: str, include_public: bool = True) -> List[Dict]:
        """Get templates for a user including public templates"""
        try:
            query = MeetingTemplate.query.filter_by(user_id=user_id)
            
            if include_public:
                # Include public templates from other users
                public_query = MeetingTemplate.query.filter(
                    MeetingTemplate.is_public == True,
                    MeetingTemplate.user_id != user_id
                )
                query = query.union(public_query)
            
            templates = query.order_by(desc(MeetingTemplate.created_at)).all()
            return [template.to_dict() for template in templates]
            
        except Exception as e:
            logger.error(f"Error getting user templates: {str(e)}")
            return []
    
    @staticmethod
    def get_template_by_id(template_id: str, user_id: str = None) -> Optional[MeetingTemplate]:
        """Get a specific template by ID"""
        try:
            query = MeetingTemplate.query.filter_by(id=template_id)
            
            # If user_id provided, ensure user has access
            if user_id:
                query = query.filter(
                    or_(
                        MeetingTemplate.user_id == user_id,
                        MeetingTemplate.is_public == True
                    )
                )
            
            return query.first()
        except Exception as e:
            logger.error(f"Error getting template by ID: {str(e)}")
            return None
    
    @staticmethod
    def update_template(template_id: str, user_id: str, **kwargs) -> Tuple[bool, any]:
        """Update template information"""
        try:
            template = MeetingTemplate.query.filter_by(id=template_id, user_id=user_id).first()
            if not template:
                return False, "Template not found"
            
            # Update allowed fields
            allowed_fields = [
                'name', 'description', 'category', 'sections', 
                'formatting_options', 'is_public'
            ]
            
            for field, value in kwargs.items():
                if field in allowed_fields and value is not None:
                    setattr(template, field, value)
            
            template.updated_at = datetime.now(timezone.utc)
            db.session.commit()
            
            logger.info(f"Template updated: {template.name}")
            return True, template
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Template update error: {str(e)}")
            return False, "Failed to update template"
    
    @staticmethod
    def delete_template(template_id: str, user_id: str) -> Tuple[bool, str]:
        """Delete a template"""
        try:
            template = MeetingTemplate.query.filter_by(id=template_id, user_id=user_id).first()
            if not template:
                return False, "Template not found"
            
            name = template.name
            db.session.delete(template)
            db.session.commit()
            
            logger.info(f"Template deleted: {name}")
            return True, "Template deleted successfully"
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Template deletion error: {str(e)}")
            return False, "Failed to delete template"
    
    @staticmethod
    def duplicate_template(template_id: str, user_id: str, new_name: str = None) -> Tuple[bool, any]:
        """Duplicate an existing template"""
        try:
            original = TemplateService.get_template_by_id(template_id, user_id)
            if not original:
                return False, "Template not found"
            
            # Create new template with copied data
            name = new_name or f"{original.name} (Copy)"
            
            success, result = TemplateService.create_template(
                user_id=user_id,
                name=name,
                description=original.description,
                category=original.category,
                sections=original.sections.copy(),
                formatting_options=original.formatting_options.copy(),
                is_public=False  # Copies are private by default
            )
            
            if success:
                logger.info(f"Template duplicated: {original.name} -> {name}")
            
            return success, result
            
        except Exception as e:
            logger.error(f"Template duplication error: {str(e)}")
            return False, "Failed to duplicate template"
    
    @staticmethod
    def create_default_templates(user_id: str) -> List[MeetingTemplate]:
        """Create default templates for a new user"""
        created_templates = []
        
        for template_key, template_data in TemplateService.DEFAULT_TEMPLATES.items():
            try:
                success, template = TemplateService.create_template(
                    user_id=user_id,
                    name=template_data['name'],
                    description=template_data['description'],
                    category=template_data['category'],
                    sections=template_data['sections'],
                    formatting_options=template_data['formatting_options'],
                    is_public=False
                )
                
                if success:
                    created_templates.append(template)
                    
            except Exception as e:
                logger.error(f"Error creating default template {template_key}: {str(e)}")
        
        logger.info(f"Created {len(created_templates)} default templates for user {user_id}")
        return created_templates
    
    @staticmethod
    def _get_default_sections() -> dict:
        """Get default sections configuration"""
        return {
            'header': {'enabled': True, 'include_date': True, 'include_attendees': True},
            'agenda': {'enabled': True, 'auto_extract': True},
            'action_items': {'enabled': True, 'include_assignee': True},
            'decisions': {'enabled': True},
            'transcript': {'enabled': False, 'summary_only': True}
        }
    
    @staticmethod
    def _get_default_formatting() -> dict:
        """Get default formatting options"""
        return {
            'style': 'professional',
            'font_family': 'Arial',
            'font_size': 11,
            'line_spacing': 1.2
        }
