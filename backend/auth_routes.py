"""
Authentication routes for MinuteMate
Handles user registration, login, logout, and profile management
"""

import logging
from flask import Blueprint, request, jsonify, session
from flask_login import login_required, current_user
from flask_jwt_extended import jwt_required, get_jwt_identity
from auth_service import AuthService
from models import db, User

logger = logging.getLogger(__name__)

# Create authentication blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

def create_response(success, message, data=None):
    """Create standardized API response"""
    response = {
        'success': success,
        'message': message
    }
    if data is not None:
        response['data'] = data
    return response

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['email', 'username', 'password', 'first_name', 'last_name']
        for field in required_fields:
            if not data.get(field):
                return jsonify(create_response(False, f"{field.replace('_', ' ').title()} is required")), 400
        
        # Register user
        success, result = AuthService.register_user(
            email=data['email'],
            username=data['username'],
            password=data['password'],
            first_name=data['first_name'],
            last_name=data['last_name']
        )
        
        if success:
            user = result
            return jsonify(create_response(
                True, 
                "Registration successful", 
                {'user': user.to_dict()}
            )), 201
        else:
            return jsonify(create_response(False, result)), 400
            
    except Exception as e:
        logger.error(f"Registration endpoint error: {str(e)}")
        return jsonify(create_response(False, "Registration failed")), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """Authenticate user and create session"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('login') or not data.get('password'):
            return jsonify(create_response(False, "Email/username and password are required")), 400
        
        # Authenticate user
        success, result = AuthService.authenticate_user(
            login_identifier=data['login'],
            password=data['password']
        )
        
        if success:
            user = result
            remember = data.get('remember', False)
            
            # Create session
            login_success, login_message = AuthService.login_user_session(user, remember)
            if login_success:
                # Create JWT tokens
                access_token, refresh_token = AuthService.create_tokens(user)
                
                response_data = {
                    'user': user.to_dict(),
                    'access_token': access_token,
                    'refresh_token': refresh_token
                }
                
                return jsonify(create_response(True, "Login successful", response_data)), 200
            else:
                return jsonify(create_response(False, login_message)), 500
        else:
            return jsonify(create_response(False, result)), 401
            
    except Exception as e:
        logger.error(f"Login endpoint error: {str(e)}")
        return jsonify(create_response(False, "Login failed")), 500

@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    """Log out current user"""
    try:
        success, message = AuthService.logout_user_session()
        if success:
            return jsonify(create_response(True, message)), 200
        else:
            return jsonify(create_response(False, message)), 500
    except Exception as e:
        logger.error(f"Logout endpoint error: {str(e)}")
        return jsonify(create_response(False, "Logout failed")), 500

@auth_bp.route('/me', methods=['GET'])
@login_required
def get_current_user():
    """Get current user information"""
    try:
        user = AuthService.get_current_user()
        if user:
            return jsonify(create_response(True, "User retrieved", {'user': user.to_dict()})), 200
        else:
            return jsonify(create_response(False, "User not found")), 404
    except Exception as e:
        logger.error(f"Get current user error: {str(e)}")
        return jsonify(create_response(False, "Failed to get user")), 500

@auth_bp.route('/profile', methods=['PUT'])
@login_required
def update_profile():
    """Update user profile"""
    try:
        data = request.get_json()
        user = AuthService.get_current_user()
        
        if not user:
            return jsonify(create_response(False, "User not found")), 404
        
        # Update profile
        success, result = AuthService.update_user_profile(
            user_id=user.id,
            first_name=data.get('first_name'),
            last_name=data.get('last_name'),
            theme=data.get('theme'),
            timezone=data.get('timezone')
        )
        
        if success:
            updated_user = result
            return jsonify(create_response(
                True, 
                "Profile updated successfully", 
                {'user': updated_user.to_dict()}
            )), 200
        else:
            return jsonify(create_response(False, result)), 400
            
    except Exception as e:
        logger.error(f"Profile update endpoint error: {str(e)}")
        return jsonify(create_response(False, "Profile update failed")), 500

@auth_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    """Change user password"""
    try:
        data = request.get_json()
        user = AuthService.get_current_user()
        
        if not user:
            return jsonify(create_response(False, "User not found")), 404
        
        # Validate required fields
        if not data.get('current_password') or not data.get('new_password'):
            return jsonify(create_response(False, "Current and new passwords are required")), 400
        
        # Change password
        success, message = AuthService.change_password(
            user_id=user.id,
            current_password=data['current_password'],
            new_password=data['new_password']
        )
        
        if success:
            return jsonify(create_response(True, message)), 200
        else:
            return jsonify(create_response(False, message)), 400
            
    except Exception as e:
        logger.error(f"Change password endpoint error: {str(e)}")
        return jsonify(create_response(False, "Password change failed")), 500

@auth_bp.route('/check', methods=['GET'])
def check_auth():
    """Check if user is authenticated"""
    try:
        if current_user.is_authenticated:
            return jsonify(create_response(
                True, 
                "User is authenticated", 
                {'user': current_user.to_dict()}
            )), 200
        else:
            return jsonify(create_response(False, "User not authenticated")), 401
    except Exception as e:
        logger.error(f"Auth check error: {str(e)}")
        return jsonify(create_response(False, "Auth check failed")), 500

@auth_bp.route('/deactivate', methods=['POST'])
@login_required
def deactivate_account():
    """Deactivate user account"""
    try:
        data = request.get_json()
        user = AuthService.get_current_user()
        
        if not user:
            return jsonify(create_response(False, "User not found")), 404
        
        # Verify password for security
        if not data.get('password'):
            return jsonify(create_response(False, "Password confirmation required")), 400
        
        if not user.check_password(data['password']):
            return jsonify(create_response(False, "Invalid password")), 401
        
        # Deactivate account
        success, message = AuthService.deactivate_user(user.id)
        
        if success:
            # Log out user
            AuthService.logout_user_session()
            return jsonify(create_response(True, message)), 200
        else:
            return jsonify(create_response(False, message)), 500
            
    except Exception as e:
        logger.error(f"Account deactivation error: {str(e)}")
        return jsonify(create_response(False, "Account deactivation failed")), 500

# Error handlers for the auth blueprint
@auth_bp.errorhandler(400)
def bad_request(error):
    return jsonify(create_response(False, "Bad request")), 400

@auth_bp.errorhandler(401)
def unauthorized(error):
    return jsonify(create_response(False, "Unauthorized")), 401

@auth_bp.errorhandler(403)
def forbidden(error):
    return jsonify(create_response(False, "Forbidden")), 403

@auth_bp.errorhandler(404)
def not_found(error):
    return jsonify(create_response(False, "Not found")), 404

@auth_bp.errorhandler(500)
def internal_error(error):
    return jsonify(create_response(False, "Internal server error")), 500
