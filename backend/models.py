"""
Database models for MinuteMate application
"""

from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
import hashlib
import os

db = SQLAlchemy()

class User(UserMixin, db.Model):
    """User model for authentication and user management"""
    
    __tablename__ = 'users'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    
    # Account status
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_verified = db.Column(db.Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), 
                          onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    last_login = db.Column(db.DateTime)
    
    # User preferences
    theme = db.Column(db.String(20), default='light', nullable=False)
    timezone = db.Column(db.String(50), default='UTC', nullable=False)
    
    # Relationships
    meetings = db.relationship('Meeting', backref='user', lazy=True, cascade='all, delete-orphan')
    templates = db.relationship('MeetingTemplate', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Set password hash using compatible method"""
        try:
            # Use werkzeug's generate_password_hash with pbkdf2 (most compatible)
            self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')
            print(f"DEBUG: Password hash set using werkzeug: {self.password_hash[:50]}...")
        except Exception as e:
            print(f"DEBUG: Werkzeug password hashing failed: {e}")
            # Fallback to simple pbkdf2 if werkzeug fails
            salt = os.urandom(32)
            pwdhash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
            self.password_hash = salt.hex() + ':' + pwdhash.hex()
            print(f"DEBUG: Password hash set using custom pbkdf2: {self.password_hash[:50]}...")

    def check_password(self, password):
        """Check password against hash"""
        try:
            print(f"DEBUG: Checking password for user, hash starts with: {self.password_hash[:50]}...")
            print(f"DEBUG: Password hash contains colon: {':' in self.password_hash}")

            # Try werkzeug first (should work for most cases)
            if not ':' in self.password_hash or self.password_hash.startswith('pbkdf2:'):
                result = check_password_hash(self.password_hash, password)
                print(f"DEBUG: Werkzeug password check result: {result}")
                return result
            else:
                # Handle custom pbkdf2 format (fallback)
                salt_hex, stored_hash = self.password_hash.split(':')
                salt = bytes.fromhex(salt_hex)
                pwdhash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
                result = pwdhash.hex() == stored_hash
                print(f"DEBUG: Custom pbkdf2 password check result: {result}")
                return result
        except Exception as e:
            print(f"DEBUG: Password check exception: {e}")
            return False
    
    @property
    def full_name(self):
        """Get user's full name"""
        return f"{self.first_name} {self.last_name}"
    
    def to_dict(self):
        """Convert user to dictionary (excluding sensitive data)"""
        return {
            'id': self.id,
            'email': self.email,
            'username': self.username,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.full_name,
            'is_active': self.is_active,
            'is_verified': self.is_verified,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'theme': self.theme,
            'timezone': self.timezone
        }
    
    def __repr__(self):
        return f'<User {self.username}>'


class Meeting(db.Model):
    """Meeting model for storing meeting information and results"""
    
    __tablename__ = 'meetings'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    
    # Meeting metadata
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    meeting_date = db.Column(db.DateTime)
    duration_minutes = db.Column(db.Integer)
    
    # File information
    original_filename = db.Column(db.String(255))
    file_size = db.Column(db.Integer)
    file_type = db.Column(db.String(50))
    
    # Processing information
    job_id = db.Column(db.String(36), unique=True, index=True)
    status = db.Column(db.String(50), default='pending', nullable=False)
    processing_time_seconds = db.Column(db.Float)
    
    # AI Results
    transcript = db.Column(db.Text)
    attendees = db.Column(db.JSON)
    agenda_items = db.Column(db.JSON)
    motions = db.Column(db.JSON)
    action_items = db.Column(db.JSON)
    key_decisions = db.Column(db.JSON)
    
    # Generated files
    docx_file_path = db.Column(db.String(500))
    html_file_path = db.Column(db.String(500))
    json_file_path = db.Column(db.String(500))
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), 
                          onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Template used
    template_id = db.Column(db.String(36), db.ForeignKey('meeting_templates.id'))
    
    def to_dict(self):
        """Convert meeting to dictionary"""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'meeting_date': self.meeting_date.isoformat() if self.meeting_date else None,
            'duration_minutes': self.duration_minutes,
            'original_filename': self.original_filename,
            'file_size': self.file_size,
            'file_type': self.file_type,
            'job_id': self.job_id,
            'status': self.status,
            'processing_time_seconds': self.processing_time_seconds,
            'attendees': self.attendees,
            'agenda_items': self.agenda_items,
            'motions': self.motions,
            'action_items': self.action_items,
            'key_decisions': self.key_decisions,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<Meeting {self.title}>'


class MeetingTemplate(db.Model):
    """Template model for customizable meeting formats"""
    
    __tablename__ = 'meeting_templates'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    
    # Template metadata
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(50), default='general', nullable=False)  # board, team, project, etc.
    
    # Template configuration
    is_public = db.Column(db.Boolean, default=False, nullable=False)
    is_default = db.Column(db.Boolean, default=False, nullable=False)
    
    # Template structure
    sections = db.Column(db.JSON, nullable=False)  # Defines which sections to include
    formatting_options = db.Column(db.JSON)  # Styling and format preferences
    
    # Usage tracking
    usage_count = db.Column(db.Integer, default=0, nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), 
                          onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    meetings = db.relationship('Meeting', backref='template', lazy=True)
    
    def to_dict(self):
        """Convert template to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'is_public': self.is_public,
            'is_default': self.is_default,
            'sections': self.sections,
            'formatting_options': self.formatting_options,
            'usage_count': self.usage_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<MeetingTemplate {self.name}>'


class CalendarIntegration(db.Model):
    """Calendar integration model for storing user calendar connections"""

    __tablename__ = 'calendar_integrations'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)

    # Provider information
    provider = db.Column(db.String(50), nullable=False)  # google, outlook, apple, etc.
    provider_user_id = db.Column(db.String(255))  # User ID from the provider
    provider_email = db.Column(db.String(255))  # Email associated with the calendar

    # OAuth tokens
    access_token = db.Column(db.Text)  # Encrypted access token
    refresh_token = db.Column(db.Text)  # Encrypted refresh token
    token_expires_at = db.Column(db.DateTime)

    # Integration settings
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    sync_enabled = db.Column(db.Boolean, default=True, nullable=False)
    auto_import_events = db.Column(db.Boolean, default=False, nullable=False)

    # Sync information
    last_sync_at = db.Column(db.DateTime)
    sync_status = db.Column(db.String(50), default='connected')  # connected, error, expired
    sync_error_message = db.Column(db.Text)

    # Timestamps
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                          onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    user = db.relationship('User', backref='calendar_integrations')

    def to_dict(self):
        """Convert calendar integration to dictionary (excluding sensitive data)"""
        return {
            'id': self.id,
            'provider': self.provider,
            'provider_email': self.provider_email,
            'is_active': self.is_active,
            'sync_enabled': self.sync_enabled,
            'auto_import_events': self.auto_import_events,
            'last_sync_at': self.last_sync_at.isoformat() if self.last_sync_at else None,
            'sync_status': self.sync_status,
            'sync_error_message': self.sync_error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self):
        return f'<CalendarIntegration {self.provider} - {self.provider_email}>'


class CalendarEvent(db.Model):
    """Calendar event model for storing imported calendar events"""

    __tablename__ = 'calendar_events'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    integration_id = db.Column(db.String(36), db.ForeignKey('calendar_integrations.id'), nullable=False)

    # Event information
    title = db.Column(db.String(500), nullable=False)
    description = db.Column(db.Text)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    location = db.Column(db.String(500))
    attendees = db.Column(db.JSON)  # List of attendee emails

    # Provider information
    provider_event_id = db.Column(db.String(255), nullable=False)
    provider_url = db.Column(db.String(1000))  # Link to event in provider's calendar

    # Meeting association
    meeting_id = db.Column(db.String(36), db.ForeignKey('meetings.id'))  # Associated meeting if any

    # Event status
    is_imported = db.Column(db.Boolean, default=True, nullable=False)
    is_processed = db.Column(db.Boolean, default=False, nullable=False)  # Has been processed for minutes

    # Timestamps
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                          onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    provider_created_at = db.Column(db.DateTime)
    provider_updated_at = db.Column(db.DateTime)

    # Relationships
    user = db.relationship('User', backref='calendar_events')
    integration = db.relationship('CalendarIntegration', backref='events')
    meeting = db.relationship('Meeting', backref='calendar_event', uselist=False)

    def to_dict(self):
        """Convert calendar event to dictionary"""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'location': self.location,
            'attendees': self.attendees,
            'provider_event_id': self.provider_event_id,
            'provider_url': self.provider_url,
            'meeting_id': self.meeting_id,
            'is_imported': self.is_imported,
            'is_processed': self.is_processed,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'provider_created_at': self.provider_created_at.isoformat() if self.provider_created_at else None,
            'provider_updated_at': self.provider_updated_at.isoformat() if self.provider_updated_at else None
        }

    def __repr__(self):
        return f'<CalendarEvent {self.title}>'
