"""
Authentication service for MinuteMate
Handles user registration, login, and session management
"""

import logging
import secrets
from datetime import datetime, timezone, timedelta
from flask import current_app
from flask_login import login_user, logout_user, current_user
from flask_jwt_extended import create_access_token, create_refresh_token, get_jwt_identity
from models import db, User
import re

logger = logging.getLogger(__name__)

class AuthService:
    """Service for handling authentication operations"""
    
    @staticmethod
    def validate_email(email):
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
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
    
    @staticmethod
    def validate_username(username):
        """Validate username format"""
        if len(username) < 3:
            return False, "Username must be at least 3 characters long"
        
        if len(username) > 20:
            return False, "Username must be no more than 20 characters long"
        
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            return False, "Username can only contain letters, numbers, and underscores"
        
        return True, "Username is valid"
    
    @staticmethod
    def register_user(email, username, password, first_name, last_name):
        """Register a new user"""
        try:
            # Validate input
            if not AuthService.validate_email(email):
                return False, "Invalid email format"
            
            username_valid, username_msg = AuthService.validate_username(username)
            if not username_valid:
                return False, username_msg
            
            password_valid, password_msg = AuthService.validate_password(password)
            if not password_valid:
                return False, password_msg
            
            if not first_name or not first_name.strip():
                return False, "First name is required"
            
            if not last_name or not last_name.strip():
                return False, "Last name is required"
            
            # Check if user already exists
            if User.query.filter_by(email=email.lower()).first():
                return False, "Email already registered"
            
            if User.query.filter_by(username=username.lower()).first():
                return False, "Username already taken"
            
            # Create new user
            user = User(
                email=email.lower(),
                username=username.lower(),
                first_name=first_name.strip(),
                last_name=last_name.strip()
            )
            user.set_password(password)
            
            db.session.add(user)
            db.session.commit()
            
            logger.info(f"New user registered: {user.username} ({user.email})")
            return True, user
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Registration error: {str(e)}")
            return False, "Registration failed. Please try again."
    
    @staticmethod
    def authenticate_user(login_identifier, password):
        """Authenticate user with email/username and password"""
        try:
            # Find user by email or username
            user = User.query.filter(
                (User.email == login_identifier.lower()) |
                (User.username == login_identifier.lower())
            ).first()

            if not user:
                logger.error(f"User not found for login identifier: {login_identifier}")
                return False, "Invalid credentials"

            logger.info(f"Found user for authentication: {user.username} ({user.email})")
            
            if not user.is_active:
                return False, "Account is deactivated"
            
            if not user.check_password(password):
                logger.error(f"Password check failed for user: {user.username}")
                return False, "Invalid credentials"
            
            # Update last login
            user.last_login = datetime.now(timezone.utc)
            db.session.commit()
            
            logger.info(f"User authenticated: {user.username}")
            return True, user
            
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            return False, "Authentication failed. Please try again."
    
    @staticmethod
    def login_user_session(user, remember=False):
        """Log in user and create session"""
        try:
            login_user(user, remember=remember)
            logger.info(f"User logged in: {user.username}")
            return True, "Login successful"
        except Exception as e:
            logger.error(f"Login session error: {str(e)}")
            return False, "Login failed"
    
    @staticmethod
    def logout_user_session():
        """Log out current user"""
        try:
            if current_user.is_authenticated:
                username = current_user.username
                logout_user()
                logger.info(f"User logged out: {username}")
            return True, "Logout successful"
        except Exception as e:
            logger.error(f"Logout error: {str(e)}")
            return False, "Logout failed"
    
    @staticmethod
    def create_tokens(user):
        """Create JWT access and refresh tokens"""
        try:
            access_token = create_access_token(
                identity=user.id,
                expires_delta=timedelta(hours=1)
            )
            refresh_token = create_refresh_token(
                identity=user.id,
                expires_delta=timedelta(days=30)
            )
            return access_token, refresh_token
        except Exception as e:
            logger.error(f"Token creation error: {str(e)}")
            return None, None
    
    @staticmethod
    def get_current_user():
        """Get current authenticated user"""
        if current_user.is_authenticated:
            return current_user
        return None
    
    @staticmethod
    def update_user_profile(user_id, **kwargs):
        """Update user profile information"""
        try:
            user = User.query.get(user_id)
            if not user:
                return False, "User not found"
            
            # Update allowed fields
            allowed_fields = ['first_name', 'last_name', 'theme', 'timezone']
            for field, value in kwargs.items():
                if field in allowed_fields and value is not None:
                    setattr(user, field, value)
            
            user.updated_at = datetime.now(timezone.utc)
            db.session.commit()
            
            logger.info(f"User profile updated: {user.username}")
            return True, user
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Profile update error: {str(e)}")
            return False, "Profile update failed"
    
    @staticmethod
    def change_password(user_id, current_password, new_password):
        """Change user password"""
        try:
            user = User.query.get(user_id)
            if not user:
                return False, "User not found"
            
            if not user.check_password(current_password):
                return False, "Current password is incorrect"
            
            password_valid, password_msg = AuthService.validate_password(new_password)
            if not password_valid:
                return False, password_msg
            
            user.set_password(new_password)
            user.updated_at = datetime.now(timezone.utc)
            db.session.commit()
            
            logger.info(f"Password changed for user: {user.username}")
            return True, "Password changed successfully"
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Password change error: {str(e)}")
            return False, "Password change failed"
    
    @staticmethod
    def deactivate_user(user_id):
        """Deactivate user account"""
        try:
            user = User.query.get(user_id)
            if not user:
                return False, "User not found"
            
            user.is_active = False
            user.updated_at = datetime.now(timezone.utc)
            db.session.commit()
            
            logger.info(f"User deactivated: {user.username}")
            return True, "Account deactivated"

        except Exception as e:
            db.session.rollback()
            logger.error(f"User deactivation error: {str(e)}")
            return False, "Deactivation failed"

    def request_password_reset(self, email):
        """Request a password reset for the given email"""
        try:
            user = User.query.filter_by(email=email).first()
            if not user:
                # Don't reveal if email exists or not for security
                return {'success': True, 'message': 'If the email exists, a reset link has been sent'}

            # Generate reset token
            reset_token = secrets.token_urlsafe(32)
            reset_expires = datetime.now() + timedelta(hours=1)  # 1 hour expiry

            # Store reset token (in a real app, you'd store this in the database)
            # For now, we'll use a simple in-memory store
            if not hasattr(self, 'reset_tokens'):
                self.reset_tokens = {}

            self.reset_tokens[reset_token] = {
                'user_id': user.id,
                'email': email,
                'expires': reset_expires
            }

            # In a real application, you would send an email here
            # For development, we'll just log the reset link
            reset_url = f"http://localhost:5000/frontend/auth.html?reset_token={reset_token}"
            logger.info(f"Password reset requested for {email}")
            logger.info(f"Reset URL: {reset_url}")

            return {
                'success': True,
                'message': 'Password reset link sent to your email',
                'reset_url': reset_url  # Only for development
            }

        except Exception as e:
            logger.error(f"Error requesting password reset: {e}")
            return {'success': False, 'message': 'Failed to process password reset request'}

    def reset_password(self, reset_token, new_password):
        """Reset password using a reset token"""
        try:
            if not hasattr(self, 'reset_tokens') or reset_token not in self.reset_tokens:
                return {'success': False, 'message': 'Invalid or expired reset token'}

            token_data = self.reset_tokens[reset_token]

            # Check if token is expired
            if datetime.now() > token_data['expires']:
                del self.reset_tokens[reset_token]
                return {'success': False, 'message': 'Reset token has expired'}

            # Find user
            user = User.query.get(token_data['user_id'])
            if not user:
                return {'success': False, 'message': 'User not found'}

            # Update password
            user.set_password(new_password)
            user.updated_at = datetime.now()
            db.session.commit()

            # Remove used token
            del self.reset_tokens[reset_token]

            logger.info(f"Password reset successful for user: {user.email}")
            return {'success': True, 'message': 'Password reset successfully'}

        except Exception as e:
            logger.error(f"Error resetting password: {e}")
            return {'success': False, 'message': 'Failed to reset password'}
