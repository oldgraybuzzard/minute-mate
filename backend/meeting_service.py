"""
Meeting service for MinuteMate
Handles meeting management, history, and dashboard operations
"""

import logging
from datetime import datetime, timezone
from flask_login import current_user
from models import db, Meeting, User
from sqlalchemy import desc, or_
from typing import List, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

class MeetingService:
    """Service for handling meeting operations"""
    
    @staticmethod
    def create_meeting(user_id: str, title: str, description: str = None, 
                      meeting_date: datetime = None, job_id: str = None) -> Tuple[bool, any]:
        """Create a new meeting record"""
        try:
            meeting = Meeting(
                user_id=user_id,
                title=title,
                description=description,
                meeting_date=meeting_date or datetime.now(timezone.utc),
                job_id=job_id,
                status='pending'
            )
            
            db.session.add(meeting)
            db.session.commit()
            
            logger.info(f"Meeting created: {meeting.title} for user {user_id}")
            return True, meeting
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Meeting creation error: {str(e)}")
            return False, "Failed to create meeting"
    
    @staticmethod
    def get_user_meetings(user_id: str, page: int = 1, per_page: int = 20, 
                         search: str = None, status: str = None) -> Dict:
        """Get paginated meetings for a user with optional filtering"""
        try:
            query = Meeting.query.filter_by(user_id=user_id)
            
            # Apply search filter
            if search:
                search_term = f"%{search}%"
                query = query.filter(
                    or_(
                        Meeting.title.ilike(search_term),
                        Meeting.description.ilike(search_term),
                        Meeting.original_filename.ilike(search_term)
                    )
                )
            
            # Apply status filter
            if status and status != 'all':
                query = query.filter_by(status=status)
            
            # Order by creation date (newest first)
            query = query.order_by(desc(Meeting.created_at))
            
            # Paginate results
            pagination = query.paginate(
                page=page, 
                per_page=per_page, 
                error_out=False
            )
            
            meetings = [meeting.to_dict() for meeting in pagination.items]
            
            return {
                'meetings': meetings,
                'total': pagination.total,
                'pages': pagination.pages,
                'current_page': page,
                'per_page': per_page,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
            
        except Exception as e:
            logger.error(f"Error getting user meetings: {str(e)}")
            return {
                'meetings': [],
                'total': 0,
                'pages': 0,
                'current_page': 1,
                'per_page': per_page,
                'has_next': False,
                'has_prev': False
            }
    
    @staticmethod
    def get_meeting_by_id(meeting_id: str, user_id: str = None) -> Optional[Meeting]:
        """Get a specific meeting by ID, optionally filtered by user"""
        try:
            query = Meeting.query.filter_by(id=meeting_id)
            if user_id:
                query = query.filter_by(user_id=user_id)
            return query.first()
        except Exception as e:
            logger.error(f"Error getting meeting by ID: {str(e)}")
            return None
    
    @staticmethod
    def get_meeting_by_job_id(job_id: str, user_id: str = None) -> Optional[Meeting]:
        """Get a meeting by job ID, optionally filtered by user"""
        try:
            query = Meeting.query.filter_by(job_id=job_id)
            if user_id:
                query = query.filter_by(user_id=user_id)
            return query.first()
        except Exception as e:
            logger.error(f"Error getting meeting by job ID: {str(e)}")
            return None
    
    @staticmethod
    def update_meeting(meeting_id: str, user_id: str, **kwargs) -> Tuple[bool, any]:
        """Update meeting information"""
        try:
            meeting = Meeting.query.filter_by(id=meeting_id, user_id=user_id).first()
            if not meeting:
                return False, "Meeting not found"
            
            # Update allowed fields
            allowed_fields = [
                'title', 'description', 'meeting_date', 'status', 'processing_time_seconds',
                'transcript', 'attendees', 'agenda_items', 'motions', 'action_items', 
                'key_decisions', 'docx_file_path', 'html_file_path', 'json_file_path',
                'original_filename', 'file_size', 'file_type', 'duration_minutes'
            ]
            
            for field, value in kwargs.items():
                if field in allowed_fields and value is not None:
                    setattr(meeting, field, value)
            
            meeting.updated_at = datetime.now(timezone.utc)
            db.session.commit()
            
            logger.info(f"Meeting updated: {meeting.title}")
            return True, meeting
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Meeting update error: {str(e)}")
            return False, "Failed to update meeting"
    
    @staticmethod
    def delete_meeting(meeting_id: str, user_id: str) -> Tuple[bool, str]:
        """Delete a meeting"""
        try:
            meeting = Meeting.query.filter_by(id=meeting_id, user_id=user_id).first()
            if not meeting:
                return False, "Meeting not found"
            
            title = meeting.title
            db.session.delete(meeting)
            db.session.commit()
            
            logger.info(f"Meeting deleted: {title}")
            return True, "Meeting deleted successfully"
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Meeting deletion error: {str(e)}")
            return False, "Failed to delete meeting"
    
    @staticmethod
    def get_user_statistics(user_id: str) -> Dict:
        """Get meeting statistics for a user"""
        try:
            total_meetings = Meeting.query.filter_by(user_id=user_id).count()
            completed_meetings = Meeting.query.filter_by(user_id=user_id, status='completed').count()
            pending_meetings = Meeting.query.filter_by(user_id=user_id, status='pending').count()
            processing_meetings = Meeting.query.filter_by(user_id=user_id, status='processing').count()
            
            # Get recent meetings (last 7 days)
            from datetime import timedelta
            week_ago = datetime.now(timezone.utc) - timedelta(days=7)
            recent_meetings = Meeting.query.filter(
                Meeting.user_id == user_id,
                Meeting.created_at >= week_ago
            ).count()
            
            # Calculate average processing time for completed meetings
            completed_with_time = Meeting.query.filter(
                Meeting.user_id == user_id,
                Meeting.status == 'completed',
                Meeting.processing_time_seconds.isnot(None)
            ).all()
            
            avg_processing_time = 0
            if completed_with_time:
                total_time = sum(m.processing_time_seconds for m in completed_with_time)
                avg_processing_time = total_time / len(completed_with_time)
            
            return {
                'total_meetings': total_meetings,
                'completed_meetings': completed_meetings,
                'pending_meetings': pending_meetings,
                'processing_meetings': processing_meetings,
                'recent_meetings': recent_meetings,
                'avg_processing_time': round(avg_processing_time, 2),
                'success_rate': round((completed_meetings / total_meetings * 100) if total_meetings > 0 else 0, 1)
            }
            
        except Exception as e:
            logger.error(f"Error getting user statistics: {str(e)}")
            return {
                'total_meetings': 0,
                'completed_meetings': 0,
                'pending_meetings': 0,
                'processing_meetings': 0,
                'recent_meetings': 0,
                'avg_processing_time': 0,
                'success_rate': 0
            }
    
    @staticmethod
    def get_recent_meetings(user_id: str, limit: int = 5) -> List[Dict]:
        """Get recent meetings for dashboard"""
        try:
            meetings = Meeting.query.filter_by(user_id=user_id)\
                .order_by(desc(Meeting.created_at))\
                .limit(limit)\
                .all()
            
            return [meeting.to_dict() for meeting in meetings]
            
        except Exception as e:
            logger.error(f"Error getting recent meetings: {str(e)}")
            return []
    
    @staticmethod
    def search_meetings(user_id: str, query: str, limit: int = 10) -> List[Dict]:
        """Search meetings by title, description, or content"""
        try:
            search_term = f"%{query}%"
            meetings = Meeting.query.filter(
                Meeting.user_id == user_id,
                or_(
                    Meeting.title.ilike(search_term),
                    Meeting.description.ilike(search_term),
                    Meeting.transcript.ilike(search_term)
                )
            ).order_by(desc(Meeting.created_at))\
             .limit(limit)\
             .all()
            
            return [meeting.to_dict() for meeting in meetings]
            
        except Exception as e:
            logger.error(f"Error searching meetings: {str(e)}")
            return []
