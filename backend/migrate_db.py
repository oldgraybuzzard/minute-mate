"""
Database migration script for MinuteMate
Adds missing columns to existing database
"""

import sqlite3
import os
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

def get_db_path():
    """Get the database path"""
    return os.path.join(os.path.dirname(__file__), 'minutemate.db')

def check_column_exists(cursor, table_name, column_name):
    """Check if a column exists in a table"""
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [column[1] for column in cursor.fetchall()]
    return column_name in columns

def migrate_database():
    """Migrate the database to add missing columns"""
    db_path = get_db_path()
    
    if not os.path.exists(db_path):
        print("Database file not found. No migration needed.")
        return
    
    print(f"Migrating database: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        migrations_applied = []
        
        # Check and add language column to users table
        if not check_column_exists(cursor, 'users', 'language'):
            print("Adding 'language' column to users table...")
            cursor.execute("ALTER TABLE users ADD COLUMN language VARCHAR(10) DEFAULT 'en' NOT NULL")
            migrations_applied.append("Added 'language' column to users table")
        
        # Check and add updated_at column to users table if missing
        if not check_column_exists(cursor, 'users', 'updated_at'):
            print("Adding 'updated_at' column to users table...")
            cursor.execute("ALTER TABLE users ADD COLUMN updated_at DATETIME")
            # Update existing records with current timestamp
            current_time = datetime.now(timezone.utc).isoformat()
            cursor.execute("UPDATE users SET updated_at = ? WHERE updated_at IS NULL", (current_time,))
            migrations_applied.append("Added 'updated_at' column to users table")
        
        # Check and add batch_job_id column to meetings table if missing
        if not check_column_exists(cursor, 'meetings', 'batch_job_id'):
            print("Adding 'batch_job_id' column to meetings table...")
            cursor.execute("ALTER TABLE meetings ADD COLUMN batch_job_id VARCHAR(36)")
            migrations_applied.append("Added 'batch_job_id' column to meetings table")

        # Check and add document comparison columns to meetings table
        if not check_column_exists(cursor, 'meetings', 'edited_document_path'):
            print("Adding 'edited_document_path' column to meetings table...")
            cursor.execute("ALTER TABLE meetings ADD COLUMN edited_document_path VARCHAR(500)")
            migrations_applied.append("Added 'edited_document_path' column to meetings table")

        if not check_column_exists(cursor, 'meetings', 'comparison_data'):
            print("Adding 'comparison_data' column to meetings table...")
            cursor.execute("ALTER TABLE meetings ADD COLUMN comparison_data TEXT")
            migrations_applied.append("Added 'comparison_data' column to meetings table")

        if not check_column_exists(cursor, 'meetings', 'preferences_learned'):
            print("Adding 'preferences_learned' column to meetings table...")
            cursor.execute("ALTER TABLE meetings ADD COLUMN preferences_learned BOOLEAN DEFAULT 0")
            migrations_applied.append("Added 'preferences_learned' column to meetings table")
        
        # Create batch_jobs table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS batch_jobs (
                id VARCHAR(36) PRIMARY KEY,
                user_id VARCHAR(36) NOT NULL,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                total_files INTEGER DEFAULT 0 NOT NULL,
                uploaded_files INTEGER DEFAULT 0 NOT NULL,
                processed_files INTEGER DEFAULT 0 NOT NULL,
                failed_files INTEGER DEFAULT 0 NOT NULL,
                template_id VARCHAR(36),
                processing_options JSON,
                files_data JSON,
                status VARCHAR(50) DEFAULT 'created' NOT NULL,
                error_message TEXT,
                created_at DATETIME NOT NULL,
                started_at DATETIME,
                completed_at DATETIME,
                updated_at DATETIME NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (template_id) REFERENCES meeting_templates(id)
            )
        """)
        
        # Check if batch_jobs table was created
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='batch_jobs'")
        if cursor.fetchone():
            migrations_applied.append("Created batch_jobs table")
        
        # Create calendar_integrations table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS calendar_integrations (
                id VARCHAR(36) PRIMARY KEY,
                user_id VARCHAR(36) NOT NULL,
                provider VARCHAR(50) NOT NULL,
                provider_user_id VARCHAR(255),
                provider_email VARCHAR(255),
                access_token TEXT,
                refresh_token TEXT,
                token_expires_at DATETIME,
                is_active BOOLEAN DEFAULT 1 NOT NULL,
                sync_enabled BOOLEAN DEFAULT 1 NOT NULL,
                auto_import_events BOOLEAN DEFAULT 0 NOT NULL,
                last_sync_at DATETIME,
                sync_status VARCHAR(50) DEFAULT 'connected',
                sync_error_message TEXT,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        # Check if calendar_integrations table was created
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='calendar_integrations'")
        if cursor.fetchone():
            migrations_applied.append("Created calendar_integrations table")
        
        # Create calendar_events table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS calendar_events (
                id VARCHAR(36) PRIMARY KEY,
                user_id VARCHAR(36) NOT NULL,
                integration_id VARCHAR(36) NOT NULL,
                title VARCHAR(500) NOT NULL,
                description TEXT,
                start_time DATETIME NOT NULL,
                end_time DATETIME NOT NULL,
                location VARCHAR(500),
                attendees JSON,
                provider_event_id VARCHAR(255) NOT NULL,
                provider_url VARCHAR(1000),
                meeting_id VARCHAR(36),
                is_imported BOOLEAN DEFAULT 1 NOT NULL,
                is_processed BOOLEAN DEFAULT 0 NOT NULL,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL,
                provider_created_at DATETIME,
                provider_updated_at DATETIME,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (integration_id) REFERENCES calendar_integrations(id),
                FOREIGN KEY (meeting_id) REFERENCES meetings(id)
            )
        """)
        
        # Check if calendar_events table was created
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='calendar_events'")
        if cursor.fetchone():
            migrations_applied.append("Created calendar_events table")

        # Create user_preferences table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_preferences (
                id VARCHAR(36) PRIMARY KEY,
                user_id VARCHAR(36) NOT NULL,
                preference_key VARCHAR(100) NOT NULL,
                preference_value TEXT NOT NULL,
                confidence_score REAL DEFAULT 0.5 NOT NULL,
                category VARCHAR(50) DEFAULT 'general' NOT NULL,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        # Check if user_preferences table was created
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_preferences'")
        if cursor.fetchone():
            migrations_applied.append("Created user_preferences table")
        
        # Commit all changes
        conn.commit()
        
        if migrations_applied:
            print("\nMigrations applied successfully:")
            for migration in migrations_applied:
                print(f"  ✓ {migration}")
        else:
            print("No migrations needed. Database is up to date.")
        
        print("\nDatabase migration completed successfully!")
        
    except Exception as e:
        print(f"Migration failed: {str(e)}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()
