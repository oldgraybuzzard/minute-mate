#!/usr/bin/env python3
"""
MinuteMate Admin CLI Tool
Provides command-line interface for user management and system administration
"""

import argparse
import sys
import os
import sqlite3
import hashlib
import secrets
from datetime import datetime
import getpass

# Add the backend directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Initialize Flask app context for database access
from flask import Flask
from models import db, User
from auth_service import AuthService

def create_app():
    """Create Flask app for CLI operations"""
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///minutemate.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'admin-cli-secret'

    db.init_app(app)
    return app

class AdminCLI:
    def __init__(self, app):
        self.app = app
        self.auth_service = AuthService()

    def list_users(self):
        """List all users in the system"""
        try:
            with self.app.app_context():
                users = User.query.order_by(User.created_at.desc()).all()

                if not users:
                    print("No users found in the system.")
                    return

                print(f"\n{'ID':<5} {'Username':<20} {'Email':<30} {'Name':<25} {'Active':<8} {'Admin':<8} {'Created':<20} {'Last Login':<20}")
                print("-" * 150)

                for user in users:
                    full_name = f"{user.first_name or ''} {user.last_name or ''}".strip()
                    active_status = "Yes" if user.is_active else "No"
                    admin_status = "Yes" if getattr(user, 'is_admin', False) else "No"
                    last_login_str = user.last_login.strftime('%Y-%m-%d %H:%M:%S') if user.last_login else "Never"
                    created_str = user.created_at.strftime('%Y-%m-%d %H:%M:%S') if user.created_at else ""

                    print(f"{user.id:<5} {user.username:<20} {user.email:<30} {full_name:<25} {active_status:<8} {admin_status:<8} {created_str:<20} {last_login_str:<20}")

        except Exception as e:
            print(f"Error listing users: {e}")
    
    def create_user(self, username, email, password=None, first_name=None, last_name=None, is_admin=False):
        """Create a new user"""
        try:
            if not password:
                password = getpass.getpass("Enter password for new user: ")
                confirm_password = getpass.getpass("Confirm password: ")
                if password != confirm_password:
                    print("Passwords do not match!")
                    return False

            with self.app.app_context():
                # Check if user already exists
                existing_user = User.query.filter(
                    (User.username == username) | (User.email == email)
                ).first()

                if existing_user:
                    print(f"❌ User with username '{username}' or email '{email}' already exists!")
                    return False

                # Create new user
                user = User(
                    username=username,
                    email=email,
                    first_name=first_name or username,
                    last_name=last_name or '',
                    is_active=True
                )

                # Set password
                user.set_password(password)

                # Set admin status if requested
                if hasattr(user, 'is_admin'):
                    user.is_admin = is_admin

                db.session.add(user)
                db.session.commit()

                print(f"✅ User '{username}' created successfully!")
                if is_admin:
                    print(f"✅ Admin privileges granted to '{username}'")
                return True

        except Exception as e:
            print(f"Error creating user: {e}")
            return False
    
    def reset_password(self, username_or_email, new_password=None):
        """Reset a user's password"""
        try:
            if not new_password:
                new_password = getpass.getpass(f"Enter new password for {username_or_email}: ")
                confirm_password = getpass.getpass("Confirm new password: ")
                if new_password != confirm_password:
                    print("Passwords do not match!")
                    return False

            with self.app.app_context():
                # Find user by username or email
                user = User.query.filter(
                    (User.username == username_or_email) | (User.email == username_or_email)
                ).first()

                if not user:
                    print(f"❌ User '{username_or_email}' not found!")
                    return False

                # Set new password
                user.set_password(new_password)
                user.updated_at = datetime.now()

                db.session.commit()
                print(f"✅ Password reset successfully for user '{user.username}' ({user.email})")
                return True

        except Exception as e:
            print(f"Error resetting password: {e}")
            return False
    
    def set_admin_status(self, username_or_email, is_admin):
        """Set or remove admin status for a user"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Find user
            cursor.execute('''
                SELECT id, username, email FROM users 
                WHERE username = ? OR email = ?
            ''', (username_or_email, username_or_email))
            
            user = cursor.fetchone()
            if not user:
                print(f"❌ User '{username_or_email}' not found!")
                return False
            
            user_id, username, email = user
            
            # Update admin status
            cursor.execute('''
                UPDATE users 
                SET is_admin = ?, updated_at = ?
                WHERE id = ?
            ''', (is_admin, datetime.now().isoformat(), user_id))
            
            conn.commit()
            status = "granted" if is_admin else "revoked"
            print(f"✅ Admin privileges {status} for user '{username}' ({email})")
            return True
            
        except Exception as e:
            print(f"Error updating admin status: {e}")
            return False
        finally:
            conn.close()
    
    def delete_user(self, username_or_email, confirm=False):
        """Delete a user (with confirmation)"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Find user
            cursor.execute('''
                SELECT id, username, email FROM users 
                WHERE username = ? OR email = ?
            ''', (username_or_email, username_or_email))
            
            user = cursor.fetchone()
            if not user:
                print(f"❌ User '{username_or_email}' not found!")
                return False
            
            user_id, username, email = user
            
            if not confirm:
                response = input(f"⚠️  Are you sure you want to delete user '{username}' ({email})? [y/N]: ")
                if response.lower() != 'y':
                    print("User deletion cancelled.")
                    return False
            
            # Delete user (this will cascade to related records)
            cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
            conn.commit()
            
            print(f"✅ User '{username}' ({email}) deleted successfully!")
            return True
            
        except Exception as e:
            print(f"Error deleting user: {e}")
            return False
        finally:
            conn.close()
    
    def activate_user(self, username_or_email):
        """Activate a user account"""
        return self._set_user_status(username_or_email, True)
    
    def deactivate_user(self, username_or_email):
        """Deactivate a user account"""
        return self._set_user_status(username_or_email, False)
    
    def _set_user_status(self, username_or_email, is_active):
        """Helper method to set user active status"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Find user
            cursor.execute('''
                SELECT id, username, email FROM users 
                WHERE username = ? OR email = ?
            ''', (username_or_email, username_or_email))
            
            user = cursor.fetchone()
            if not user:
                print(f"❌ User '{username_or_email}' not found!")
                return False
            
            user_id, username, email = user
            
            # Update status
            cursor.execute('''
                UPDATE users 
                SET is_active = ?, updated_at = ?
                WHERE id = ?
            ''', (is_active, datetime.now().isoformat(), user_id))
            
            conn.commit()
            status = "activated" if is_active else "deactivated"
            print(f"✅ User '{username}' ({email}) {status} successfully!")
            return True
            
        except Exception as e:
            print(f"Error updating user status: {e}")
            return False
        finally:
            conn.close()

def main():
    parser = argparse.ArgumentParser(description='MinuteMate Admin CLI Tool')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # List users command
    subparsers.add_parser('list', help='List all users')

    # Create user command
    create_parser = subparsers.add_parser('create', help='Create a new user')
    create_parser.add_argument('username', help='Username for the new user')
    create_parser.add_argument('email', help='Email for the new user')
    create_parser.add_argument('--password', help='Password (will prompt if not provided)')
    create_parser.add_argument('--first-name', help='First name')
    create_parser.add_argument('--last-name', help='Last name')
    create_parser.add_argument('--admin', action='store_true', help='Create as admin user')

    # Reset password command
    reset_parser = subparsers.add_parser('reset-password', help='Reset user password')
    reset_parser.add_argument('user', help='Username or email')
    reset_parser.add_argument('--password', help='New password (will prompt if not provided)')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Create Flask app and admin CLI
    app = create_app()

    with app.app_context():
        # Create tables if they don't exist
        db.create_all()

    admin = AdminCLI(app)

    try:
        if args.command == 'list':
            admin.list_users()
        elif args.command == 'create':
            admin.create_user(
                args.username,
                args.email,
                args.password,
                getattr(args, 'first_name', None),
                getattr(args, 'last_name', None),
                args.admin
            )
        elif args.command == 'reset-password':
            admin.reset_password(args.user, args.password)
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    main()
