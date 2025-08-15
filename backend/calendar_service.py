"""
Calendar service for MinuteMate
Handles calendar integration with Google Calendar, Outlook, and other providers
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional, Tuple
from abc import ABC, abstractmethod
import json
import requests
from urllib.parse import urlencode
from models import db, CalendarIntegration, CalendarEvent, Meeting, User
from flask_login import current_user

logger = logging.getLogger(__name__)

class CalendarProvider(ABC):
    """Abstract base class for calendar providers"""
    
    @abstractmethod
    def get_authorization_url(self, user_id: str, redirect_uri: str) -> str:
        """Get OAuth authorization URL"""
        pass
    
    @abstractmethod
    def exchange_code_for_tokens(self, code: str, redirect_uri: str) -> Tuple[bool, Dict]:
        """Exchange authorization code for access tokens"""
        pass
    
    @abstractmethod
    def refresh_access_token(self, refresh_token: str) -> Tuple[bool, Dict]:
        """Refresh access token using refresh token"""
        pass
    
    @abstractmethod
    def get_events(self, access_token: str, start_date: datetime, end_date: datetime) -> Tuple[bool, List[Dict]]:
        """Get calendar events for date range"""
        pass
    
    @abstractmethod
    def create_event(self, access_token: str, event_data: Dict) -> Tuple[bool, Dict]:
        """Create a new calendar event"""
        pass
    
    @abstractmethod
    def update_event(self, access_token: str, event_id: str, event_data: Dict) -> Tuple[bool, Dict]:
        """Update an existing calendar event"""
        pass

class GoogleCalendarProvider(CalendarProvider):
    """Google Calendar integration"""
    
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.auth_url = "https://accounts.google.com/o/oauth2/auth"
        self.token_url = "https://oauth2.googleapis.com/token"
        self.api_base = "https://www.googleapis.com/calendar/v3"
        self.scopes = [
            "https://www.googleapis.com/auth/calendar",
            "https://www.googleapis.com/auth/calendar.events"
        ]
    
    def get_authorization_url(self, user_id: str, redirect_uri: str) -> str:
        """Get Google OAuth authorization URL"""
        params = {
            'client_id': self.client_id,
            'redirect_uri': redirect_uri,
            'scope': ' '.join(self.scopes),
            'response_type': 'code',
            'access_type': 'offline',
            'prompt': 'consent',
            'state': user_id  # Include user_id in state for security
        }
        return f"{self.auth_url}?{urlencode(params)}"
    
    def exchange_code_for_tokens(self, code: str, redirect_uri: str) -> Tuple[bool, Dict]:
        """Exchange authorization code for Google tokens"""
        try:
            data = {
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'code': code,
                'grant_type': 'authorization_code',
                'redirect_uri': redirect_uri
            }
            
            response = requests.post(self.token_url, data=data)
            
            if response.status_code == 200:
                tokens = response.json()
                return True, tokens
            else:
                logger.error(f"Google token exchange failed: {response.text}")
                return False, {"error": "Token exchange failed"}
                
        except Exception as e:
            logger.error(f"Google token exchange error: {str(e)}")
            return False, {"error": str(e)}
    
    def refresh_access_token(self, refresh_token: str) -> Tuple[bool, Dict]:
        """Refresh Google access token"""
        try:
            data = {
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'refresh_token': refresh_token,
                'grant_type': 'refresh_token'
            }
            
            response = requests.post(self.token_url, data=data)
            
            if response.status_code == 200:
                tokens = response.json()
                return True, tokens
            else:
                logger.error(f"Google token refresh failed: {response.text}")
                return False, {"error": "Token refresh failed"}
                
        except Exception as e:
            logger.error(f"Google token refresh error: {str(e)}")
            return False, {"error": str(e)}
    
    def get_events(self, access_token: str, start_date: datetime, end_date: datetime) -> Tuple[bool, List[Dict]]:
        """Get Google Calendar events"""
        try:
            headers = {'Authorization': f'Bearer {access_token}'}
            params = {
                'timeMin': start_date.isoformat(),
                'timeMax': end_date.isoformat(),
                'singleEvents': True,
                'orderBy': 'startTime'
            }
            
            response = requests.get(f"{self.api_base}/calendars/primary/events", 
                                  headers=headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                events = data.get('items', [])
                return True, self._normalize_events(events)
            else:
                logger.error(f"Google events fetch failed: {response.text}")
                return False, []
                
        except Exception as e:
            logger.error(f"Google events fetch error: {str(e)}")
            return False, []
    
    def create_event(self, access_token: str, event_data: Dict) -> Tuple[bool, Dict]:
        """Create Google Calendar event"""
        try:
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            google_event = self._convert_to_google_format(event_data)
            
            response = requests.post(f"{self.api_base}/calendars/primary/events",
                                   headers=headers, json=google_event)
            
            if response.status_code == 200:
                event = response.json()
                return True, self._normalize_event(event)
            else:
                logger.error(f"Google event creation failed: {response.text}")
                return False, {"error": "Event creation failed"}
                
        except Exception as e:
            logger.error(f"Google event creation error: {str(e)}")
            return False, {"error": str(e)}
    
    def update_event(self, access_token: str, event_id: str, event_data: Dict) -> Tuple[bool, Dict]:
        """Update Google Calendar event"""
        try:
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            google_event = self._convert_to_google_format(event_data)
            
            response = requests.put(f"{self.api_base}/calendars/primary/events/{event_id}",
                                  headers=headers, json=google_event)
            
            if response.status_code == 200:
                event = response.json()
                return True, self._normalize_event(event)
            else:
                logger.error(f"Google event update failed: {response.text}")
                return False, {"error": "Event update failed"}
                
        except Exception as e:
            logger.error(f"Google event update error: {str(e)}")
            return False, {"error": str(e)}
    
    def _normalize_events(self, events: List[Dict]) -> List[Dict]:
        """Normalize Google events to standard format"""
        normalized = []
        for event in events:
            normalized.append(self._normalize_event(event))
        return normalized
    
    def _normalize_event(self, event: Dict) -> Dict:
        """Normalize single Google event to standard format"""
        start = event.get('start', {})
        end = event.get('end', {})
        
        return {
            'id': event.get('id'),
            'title': event.get('summary', ''),
            'description': event.get('description', ''),
            'start_time': start.get('dateTime', start.get('date')),
            'end_time': end.get('dateTime', end.get('date')),
            'location': event.get('location', ''),
            'attendees': [att.get('email') for att in event.get('attendees', [])],
            'provider': 'google',
            'provider_event_id': event.get('id'),
            'html_link': event.get('htmlLink'),
            'created': event.get('created'),
            'updated': event.get('updated')
        }
    
    def _convert_to_google_format(self, event_data: Dict) -> Dict:
        """Convert standard event format to Google Calendar format"""
        google_event = {
            'summary': event_data.get('title', ''),
            'description': event_data.get('description', ''),
            'start': {
                'dateTime': event_data.get('start_time'),
                'timeZone': 'UTC'
            },
            'end': {
                'dateTime': event_data.get('end_time'),
                'timeZone': 'UTC'
            }
        }
        
        if event_data.get('location'):
            google_event['location'] = event_data['location']
        
        if event_data.get('attendees'):
            google_event['attendees'] = [
                {'email': email} for email in event_data['attendees']
            ]
        
        return google_event

class OutlookCalendarProvider(CalendarProvider):
    """Microsoft Outlook/Office 365 Calendar integration"""
    
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.auth_url = "https://login.microsoftonline.com/common/oauth2/v2.0/authorize"
        self.token_url = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
        self.api_base = "https://graph.microsoft.com/v1.0"
        self.scopes = ["https://graph.microsoft.com/Calendars.ReadWrite"]
    
    def get_authorization_url(self, user_id: str, redirect_uri: str) -> str:
        """Get Microsoft OAuth authorization URL"""
        params = {
            'client_id': self.client_id,
            'response_type': 'code',
            'redirect_uri': redirect_uri,
            'scope': ' '.join(self.scopes),
            'state': user_id
        }
        return f"{self.auth_url}?{urlencode(params)}"
    
    def exchange_code_for_tokens(self, code: str, redirect_uri: str) -> Tuple[bool, Dict]:
        """Exchange authorization code for Microsoft tokens"""
        try:
            data = {
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'code': code,
                'grant_type': 'authorization_code',
                'redirect_uri': redirect_uri
            }
            
            response = requests.post(self.token_url, data=data)
            
            if response.status_code == 200:
                tokens = response.json()
                return True, tokens
            else:
                logger.error(f"Outlook token exchange failed: {response.text}")
                return False, {"error": "Token exchange failed"}
                
        except Exception as e:
            logger.error(f"Outlook token exchange error: {str(e)}")
            return False, {"error": str(e)}
    
    def refresh_access_token(self, refresh_token: str) -> Tuple[bool, Dict]:
        """Refresh Microsoft access token"""
        try:
            data = {
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'refresh_token': refresh_token,
                'grant_type': 'refresh_token'
            }
            
            response = requests.post(self.token_url, data=data)
            
            if response.status_code == 200:
                tokens = response.json()
                return True, tokens
            else:
                logger.error(f"Outlook token refresh failed: {response.text}")
                return False, {"error": "Token refresh failed"}
                
        except Exception as e:
            logger.error(f"Outlook token refresh error: {str(e)}")
            return False, {"error": str(e)}
    
    def get_events(self, access_token: str, start_date: datetime, end_date: datetime) -> Tuple[bool, List[Dict]]:
        """Get Outlook Calendar events"""
        try:
            headers = {'Authorization': f'Bearer {access_token}'}
            params = {
                '$filter': f"start/dateTime ge '{start_date.isoformat()}' and end/dateTime le '{end_date.isoformat()}'",
                '$orderby': 'start/dateTime'
            }
            
            response = requests.get(f"{self.api_base}/me/events", 
                                  headers=headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                events = data.get('value', [])
                return True, self._normalize_events(events)
            else:
                logger.error(f"Outlook events fetch failed: {response.text}")
                return False, []
                
        except Exception as e:
            logger.error(f"Outlook events fetch error: {str(e)}")
            return False, []
    
    def create_event(self, access_token: str, event_data: Dict) -> Tuple[bool, Dict]:
        """Create Outlook Calendar event"""
        try:
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            outlook_event = self._convert_to_outlook_format(event_data)
            
            response = requests.post(f"{self.api_base}/me/events",
                                   headers=headers, json=outlook_event)
            
            if response.status_code == 201:
                event = response.json()
                return True, self._normalize_event(event)
            else:
                logger.error(f"Outlook event creation failed: {response.text}")
                return False, {"error": "Event creation failed"}
                
        except Exception as e:
            logger.error(f"Outlook event creation error: {str(e)}")
            return False, {"error": str(e)}
    
    def update_event(self, access_token: str, event_id: str, event_data: Dict) -> Tuple[bool, Dict]:
        """Update Outlook Calendar event"""
        try:
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            outlook_event = self._convert_to_outlook_format(event_data)
            
            response = requests.patch(f"{self.api_base}/me/events/{event_id}",
                                    headers=headers, json=outlook_event)
            
            if response.status_code == 200:
                event = response.json()
                return True, self._normalize_event(event)
            else:
                logger.error(f"Outlook event update failed: {response.text}")
                return False, {"error": "Event update failed"}
                
        except Exception as e:
            logger.error(f"Outlook event update error: {str(e)}")
            return False, {"error": str(e)}
    
    def _normalize_events(self, events: List[Dict]) -> List[Dict]:
        """Normalize Outlook events to standard format"""
        normalized = []
        for event in events:
            normalized.append(self._normalize_event(event))
        return normalized
    
    def _normalize_event(self, event: Dict) -> Dict:
        """Normalize single Outlook event to standard format"""
        start = event.get('start', {})
        end = event.get('end', {})
        
        return {
            'id': event.get('id'),
            'title': event.get('subject', ''),
            'description': event.get('body', {}).get('content', ''),
            'start_time': start.get('dateTime'),
            'end_time': end.get('dateTime'),
            'location': event.get('location', {}).get('displayName', ''),
            'attendees': [att.get('emailAddress', {}).get('address') for att in event.get('attendees', [])],
            'provider': 'outlook',
            'provider_event_id': event.get('id'),
            'html_link': event.get('webLink'),
            'created': event.get('createdDateTime'),
            'updated': event.get('lastModifiedDateTime')
        }
    
    def _convert_to_outlook_format(self, event_data: Dict) -> Dict:
        """Convert standard event format to Outlook format"""
        outlook_event = {
            'subject': event_data.get('title', ''),
            'body': {
                'contentType': 'HTML',
                'content': event_data.get('description', '')
            },
            'start': {
                'dateTime': event_data.get('start_time'),
                'timeZone': 'UTC'
            },
            'end': {
                'dateTime': event_data.get('end_time'),
                'timeZone': 'UTC'
            }
        }
        
        if event_data.get('location'):
            outlook_event['location'] = {
                'displayName': event_data['location']
            }
        
        if event_data.get('attendees'):
            outlook_event['attendees'] = [
                {
                    'emailAddress': {
                        'address': email,
                        'name': email
                    }
                } for email in event_data['attendees']
            ]
        
        return outlook_event


class CalendarService:
    """Main calendar service for managing integrations and events"""

    def __init__(self):
        self.providers = {}
        self._initialize_providers()

    def _initialize_providers(self):
        """Initialize calendar providers with configuration"""
        # These would typically come from environment variables or config
        google_config = {
            'client_id': 'your-google-client-id',
            'client_secret': 'your-google-client-secret'
        }

        outlook_config = {
            'client_id': 'your-outlook-client-id',
            'client_secret': 'your-outlook-client-secret'
        }

        self.providers['google'] = GoogleCalendarProvider(
            google_config['client_id'],
            google_config['client_secret']
        )

        self.providers['outlook'] = OutlookCalendarProvider(
            outlook_config['client_id'],
            outlook_config['client_secret']
        )

    def get_available_providers(self) -> List[Dict]:
        """Get list of available calendar providers"""
        return [
            {
                'id': 'google',
                'name': 'Google Calendar',
                'description': 'Connect your Google Calendar account',
                'icon': 'fab fa-google',
                'color': '#4285f4'
            },
            {
                'id': 'outlook',
                'name': 'Microsoft Outlook',
                'description': 'Connect your Outlook/Office 365 calendar',
                'icon': 'fab fa-microsoft',
                'color': '#0078d4'
            }
        ]

    def get_authorization_url(self, provider: str, user_id: str, redirect_uri: str) -> Tuple[bool, str]:
        """Get OAuth authorization URL for a provider"""
        try:
            if provider not in self.providers:
                return False, "Unsupported calendar provider"

            auth_url = self.providers[provider].get_authorization_url(user_id, redirect_uri)
            return True, auth_url

        except Exception as e:
            logger.error(f"Authorization URL error for {provider}: {str(e)}")
            return False, str(e)

    def connect_calendar(self, provider: str, user_id: str, code: str, redirect_uri: str) -> Tuple[bool, any]:
        """Connect a calendar account using OAuth code"""
        try:
            if provider not in self.providers:
                return False, "Unsupported calendar provider"

            # Exchange code for tokens
            success, tokens = self.providers[provider].exchange_code_for_tokens(code, redirect_uri)
            if not success:
                return False, tokens.get('error', 'Token exchange failed')

            # Get user info from provider (if available)
            provider_email = self._get_provider_email(provider, tokens.get('access_token'))

            # Store integration
            integration = CalendarIntegration(
                user_id=user_id,
                provider=provider,
                provider_email=provider_email,
                access_token=self._encrypt_token(tokens.get('access_token')),
                refresh_token=self._encrypt_token(tokens.get('refresh_token')),
                token_expires_at=self._calculate_expiry(tokens.get('expires_in')),
                sync_status='connected'
            )

            db.session.add(integration)
            db.session.commit()

            logger.info(f"Calendar connected: {provider} for user {user_id}")
            return True, integration

        except Exception as e:
            db.session.rollback()
            logger.error(f"Calendar connection error: {str(e)}")
            return False, str(e)

    def get_user_integrations(self, user_id: str) -> List[Dict]:
        """Get all calendar integrations for a user"""
        try:
            integrations = CalendarIntegration.query.filter_by(user_id=user_id).all()
            return [integration.to_dict() for integration in integrations]
        except Exception as e:
            logger.error(f"Get integrations error: {str(e)}")
            return []

    def disconnect_calendar(self, integration_id: str, user_id: str) -> Tuple[bool, str]:
        """Disconnect a calendar integration"""
        try:
            integration = CalendarIntegration.query.filter_by(
                id=integration_id,
                user_id=user_id
            ).first()

            if not integration:
                return False, "Integration not found"

            # Delete associated events
            CalendarEvent.query.filter_by(integration_id=integration_id).delete()

            # Delete integration
            db.session.delete(integration)
            db.session.commit()

            logger.info(f"Calendar disconnected: {integration.provider} for user {user_id}")
            return True, "Calendar disconnected successfully"

        except Exception as e:
            db.session.rollback()
            logger.error(f"Calendar disconnection error: {str(e)}")
            return False, str(e)

    def sync_calendar_events(self, integration_id: str, days_back: int = 30, days_forward: int = 90) -> Tuple[bool, Dict]:
        """Sync events from a calendar integration"""
        try:
            integration = CalendarIntegration.query.get(integration_id)
            if not integration or not integration.is_active:
                return False, {"error": "Integration not found or inactive"}

            # Check if token needs refresh
            if self._token_needs_refresh(integration):
                success = self._refresh_integration_token(integration)
                if not success:
                    return False, {"error": "Token refresh failed"}

            # Get date range
            start_date = datetime.now(timezone.utc) - timedelta(days=days_back)
            end_date = datetime.now(timezone.utc) + timedelta(days=days_forward)

            # Get events from provider
            access_token = self._decrypt_token(integration.access_token)
            success, events = self.providers[integration.provider].get_events(
                access_token, start_date, end_date
            )

            if not success:
                integration.sync_status = 'error'
                integration.sync_error_message = 'Failed to fetch events'
                db.session.commit()
                return False, {"error": "Failed to fetch events"}

            # Store/update events
            imported_count = 0
            updated_count = 0

            for event_data in events:
                existing_event = CalendarEvent.query.filter_by(
                    integration_id=integration_id,
                    provider_event_id=event_data['provider_event_id']
                ).first()

                if existing_event:
                    # Update existing event
                    self._update_calendar_event(existing_event, event_data)
                    updated_count += 1
                else:
                    # Create new event
                    self._create_calendar_event(integration, event_data)
                    imported_count += 1

            # Update sync status
            integration.last_sync_at = datetime.now(timezone.utc)
            integration.sync_status = 'connected'
            integration.sync_error_message = None
            db.session.commit()

            result = {
                'imported_count': imported_count,
                'updated_count': updated_count,
                'total_events': len(events),
                'sync_time': integration.last_sync_at.isoformat()
            }

            logger.info(f"Calendar sync completed for {integration.provider}: {result}")
            return True, result

        except Exception as e:
            logger.error(f"Calendar sync error: {str(e)}")
            return False, {"error": str(e)}

    def get_calendar_events(self, user_id: str, start_date: datetime = None, end_date: datetime = None) -> List[Dict]:
        """Get calendar events for a user"""
        try:
            query = CalendarEvent.query.filter_by(user_id=user_id)

            if start_date:
                query = query.filter(CalendarEvent.start_time >= start_date)
            if end_date:
                query = query.filter(CalendarEvent.end_time <= end_date)

            events = query.order_by(CalendarEvent.start_time).all()
            return [event.to_dict() for event in events]

        except Exception as e:
            logger.error(f"Get calendar events error: {str(e)}")
            return []

    def create_follow_up_event(self, user_id: str, meeting_id: str, event_data: Dict) -> Tuple[bool, any]:
        """Create a follow-up calendar event from a meeting"""
        try:
            # Get user's primary calendar integration
            integration = CalendarIntegration.query.filter_by(
                user_id=user_id,
                is_active=True,
                sync_enabled=True
            ).first()

            if not integration:
                return False, "No active calendar integration found"

            # Check if token needs refresh
            if self._token_needs_refresh(integration):
                success = self._refresh_integration_token(integration)
                if not success:
                    return False, "Token refresh failed"

            # Create event in provider's calendar
            access_token = self._decrypt_token(integration.access_token)
            success, provider_event = self.providers[integration.provider].create_event(
                access_token, event_data
            )

            if not success:
                return False, provider_event.get('error', 'Event creation failed')

            # Store event locally
            calendar_event = CalendarEvent(
                user_id=user_id,
                integration_id=integration.id,
                title=event_data['title'],
                description=event_data.get('description', ''),
                start_time=datetime.fromisoformat(event_data['start_time'].replace('Z', '+00:00')),
                end_time=datetime.fromisoformat(event_data['end_time'].replace('Z', '+00:00')),
                location=event_data.get('location', ''),
                attendees=event_data.get('attendees', []),
                provider_event_id=provider_event['provider_event_id'],
                provider_url=provider_event.get('html_link'),
                meeting_id=meeting_id,
                is_imported=False  # This was created by us, not imported
            )

            db.session.add(calendar_event)
            db.session.commit()

            logger.info(f"Follow-up event created for meeting {meeting_id}")
            return True, calendar_event

        except Exception as e:
            db.session.rollback()
            logger.error(f"Follow-up event creation error: {str(e)}")
            return False, str(e)

    def _get_provider_email(self, provider: str, access_token: str) -> str:
        """Get user email from provider"""
        try:
            if provider == 'google':
                response = requests.get(
                    'https://www.googleapis.com/oauth2/v2/userinfo',
                    headers={'Authorization': f'Bearer {access_token}'}
                )
                if response.status_code == 200:
                    return response.json().get('email', '')
            elif provider == 'outlook':
                response = requests.get(
                    'https://graph.microsoft.com/v1.0/me',
                    headers={'Authorization': f'Bearer {access_token}'}
                )
                if response.status_code == 200:
                    return response.json().get('mail', response.json().get('userPrincipalName', ''))
        except Exception as e:
            logger.error(f"Get provider email error: {str(e)}")

        return ''

    def _encrypt_token(self, token: str) -> str:
        """Encrypt token for storage (implement proper encryption)"""
        # In production, use proper encryption like Fernet
        return token  # Placeholder

    def _decrypt_token(self, encrypted_token: str) -> str:
        """Decrypt token for use (implement proper decryption)"""
        # In production, use proper decryption
        return encrypted_token  # Placeholder

    def _calculate_expiry(self, expires_in: int) -> datetime:
        """Calculate token expiry time"""
        if expires_in:
            return datetime.now(timezone.utc) + timedelta(seconds=expires_in)
        return None

    def _token_needs_refresh(self, integration: CalendarIntegration) -> bool:
        """Check if token needs refresh"""
        if not integration.token_expires_at:
            return False

        # Refresh if token expires within 5 minutes
        return integration.token_expires_at <= datetime.now(timezone.utc) + timedelta(minutes=5)

    def _refresh_integration_token(self, integration: CalendarIntegration) -> bool:
        """Refresh integration token"""
        try:
            refresh_token = self._decrypt_token(integration.refresh_token)
            success, tokens = self.providers[integration.provider].refresh_access_token(refresh_token)

            if success:
                integration.access_token = self._encrypt_token(tokens.get('access_token'))
                if tokens.get('refresh_token'):
                    integration.refresh_token = self._encrypt_token(tokens.get('refresh_token'))
                integration.token_expires_at = self._calculate_expiry(tokens.get('expires_in'))
                db.session.commit()
                return True
            else:
                integration.sync_status = 'expired'
                integration.sync_error_message = 'Token refresh failed'
                db.session.commit()
                return False

        except Exception as e:
            logger.error(f"Token refresh error: {str(e)}")
            integration.sync_status = 'error'
            integration.sync_error_message = str(e)
            db.session.commit()
            return False

    def _create_calendar_event(self, integration, event_data: Dict):
        """Create a new calendar event record"""
        try:
            start_time = datetime.fromisoformat(event_data['start_time'].replace('Z', '+00:00'))
            end_time = datetime.fromisoformat(event_data['end_time'].replace('Z', '+00:00'))

            event = CalendarEvent(
                user_id=integration.user_id,
                integration_id=integration.id,
                title=event_data['title'],
                description=event_data.get('description', ''),
                start_time=start_time,
                end_time=end_time,
                location=event_data.get('location', ''),
                attendees=event_data.get('attendees', []),
                provider_event_id=event_data['provider_event_id'],
                provider_url=event_data.get('html_link'),
                provider_created_at=datetime.fromisoformat(event_data['created'].replace('Z', '+00:00')) if event_data.get('created') else None,
                provider_updated_at=datetime.fromisoformat(event_data['updated'].replace('Z', '+00:00')) if event_data.get('updated') else None
            )

            db.session.add(event)

        except Exception as e:
            logger.error(f"Create calendar event error: {str(e)}")

    def _update_calendar_event(self, event, event_data: Dict):
        """Update an existing calendar event record"""
        try:
            event.title = event_data['title']
            event.description = event_data.get('description', '')
            event.start_time = datetime.fromisoformat(event_data['start_time'].replace('Z', '+00:00'))
            event.end_time = datetime.fromisoformat(event_data['end_time'].replace('Z', '+00:00'))
            event.location = event_data.get('location', '')
            event.attendees = event_data.get('attendees', [])
            event.provider_url = event_data.get('html_link')

            if event_data.get('updated'):
                event.provider_updated_at = datetime.fromisoformat(event_data['updated'].replace('Z', '+00:00'))

        except Exception as e:
            logger.error(f"Update calendar event error: {str(e)}")
