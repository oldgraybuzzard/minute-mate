#!/usr/bin/env python3
"""
Quick user creation script for MinuteMate
"""

import sqlite3
import hashlib
import uuid
from datetime import datetime
import sys
from werkzeug.security import generate_password_hash

def create_user(username, email, password, first_name="", last_name="", is_admin=False):
    """Create a user directly in the database"""
    
    # Connect to database
    conn = sqlite3.connect('minutemate.db')
    cursor = conn.cursor()
    
    try:
        # Create users table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id VARCHAR(36) PRIMARY KEY,
                email VARCHAR(120) UNIQUE NOT NULL,
                username VARCHAR(80) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                first_name VARCHAR(50) NOT NULL,
                last_name VARCHAR(50) NOT NULL,
                is_active BOOLEAN NOT NULL DEFAULT 1,
                is_verified BOOLEAN NOT NULL DEFAULT 1,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL,
                last_login DATETIME,
                theme VARCHAR(20) NOT NULL DEFAULT 'light',
                timezone VARCHAR(50) NOT NULL DEFAULT 'UTC',
                language VARCHAR(10) NOT NULL DEFAULT 'en'
            )
        ''')
        
        # Check if user already exists
        cursor.execute('SELECT id FROM users WHERE username = ? OR email = ?', (username, email))
        if cursor.fetchone():
            print(f"❌ User with username '{username}' or email '{email}' already exists!")
            return False
        
        # Generate user ID and hash password using Werkzeug (compatible with auth system)
        user_id = str(uuid.uuid4())
        password_hash = generate_password_hash(password, method='pbkdf2:sha256')
        now = datetime.now().isoformat()
        
        # Insert user
        cursor.execute('''
            INSERT INTO users (
                id, email, username, password_hash, first_name, last_name,
                is_active, is_verified, created_at, updated_at,
                theme, timezone, language
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id, email, username, password_hash, first_name, last_name,
            True, True, now, now,
            'light', 'UTC', 'en'
        ))
        
        conn.commit()
        print(f"✅ User '{username}' created successfully!")
        print(f"   Email: {email}")
        print(f"   Name: {first_name} {last_name}")
        print(f"   ID: {user_id}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating user: {e}")
        return False
    finally:
        conn.close()

def list_users():
    """List all users in the database"""
    conn = sqlite3.connect('minutemate.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT id, username, email, first_name, last_name, 
                   is_active, created_at, last_login
            FROM users 
            ORDER BY created_at DESC
        ''')
        
        users = cursor.fetchall()
        
        if not users:
            print("No users found in the system.")
            return
            
        print(f"\n{'ID':<38} {'Username':<20} {'Email':<30} {'Name':<25} {'Active':<8} {'Created':<20}")
        print("-" * 150)
        
        for user in users:
            user_id, username, email, first_name, last_name, is_active, created_at, last_login = user
            full_name = f"{first_name or ''} {last_name or ''}".strip()
            active_status = "Yes" if is_active else "No"
            created_str = created_at[:19] if created_at else ""
            
            print(f"{user_id:<38} {username:<20} {email:<30} {full_name:<25} {active_status:<8} {created_str:<20}")
            
    except Exception as e:
        print(f"Error listing users: {e}")
    finally:
        conn.close()

def reset_password(username_or_email, new_password):
    """Reset a user's password"""
    conn = sqlite3.connect('minutemate.db')
    cursor = conn.cursor()
    
    try:
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
        
        # Hash new password using Werkzeug (compatible with auth system)
        password_hash = generate_password_hash(new_password, method='pbkdf2:sha256')
        
        # Update password
        cursor.execute('''
            UPDATE users 
            SET password_hash = ?, updated_at = ?
            WHERE id = ?
        ''', (password_hash, datetime.now().isoformat(), user_id))
        
        conn.commit()
        print(f"✅ Password reset successfully for user '{username}' ({email})")
        return True
        
    except Exception as e:
        print(f"Error resetting password: {e}")
        return False
    finally:
        conn.close()

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 create_user.py create <username> <email> <password> [first_name] [last_name]")
        print("  python3 create_user.py list")
        print("  python3 create_user.py reset <username_or_email> <new_password>")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == 'create':
        if len(sys.argv) < 5:
            print("Usage: python3 create_user.py create <username> <email> <password> [first_name] [last_name]")
            sys.exit(1)
        
        username = sys.argv[2]
        email = sys.argv[3]
        password = sys.argv[4]
        first_name = sys.argv[5] if len(sys.argv) > 5 else username
        last_name = sys.argv[6] if len(sys.argv) > 6 else ""
        
        create_user(username, email, password, first_name, last_name)
        
    elif command == 'list':
        list_users()
        
    elif command == 'reset':
        if len(sys.argv) < 4:
            print("Usage: python3 create_user.py reset <username_or_email> <new_password>")
            sys.exit(1)
        
        username_or_email = sys.argv[2]
        new_password = sys.argv[3]
        
        reset_password(username_or_email, new_password)
        
    else:
        print(f"Unknown command: {command}")
        print("Available commands: create, list, reset")
        sys.exit(1)
