# BoardMinutes Backend

The BoardMinutes backend is a comprehensive Flask-based API server that handles user authentication, file uploads, meeting processing, and provides enterprise-grade admin tools for user management and system monitoring.

## 🏗️ Architecture

```
backend/
├── app.py                          # Main Flask application
├── config.py                       # Configuration management
├── models.py                       # SQLAlchemy database models
├── auth_service.py                 # Authentication and user management
├── auth_routes.py                  # Authentication API endpoints
├── meeting_service.py              # Meeting processing logic
├── meeting_routes.py               # Meeting API endpoints
├── template_service.py             # Template management
├── template_routes.py              # Template API endpoints
├── batch_service.py                # Batch processing system
├── batch_routes.py                 # Batch processing endpoints
├── calendar_service.py             # Calendar integrations
├── calendar_routes.py              # Calendar API endpoints
├── document_comparison_service.py  # Document comparison logic
├── document_comparison_routes.py   # Document comparison endpoints
├── profile_routes.py               # User profile management
├── admin_cli.py                    # Command-line admin tools
├── create_user.py                  # Simple user creation script
├── migrate_db.py                   # Database migration utilities
├── utils.py                        # Utility functions
├── job_tracker.py                  # Job status tracking
├── validators.py                   # Input validation
├── middleware.py                   # Request/response middleware
├── security_middleware.py          # Security middleware
├── error_handlers.py               # Error handling
├── logging_config.py               # Logging configuration
├── modules/                        # Core processing modules
│   ├── __init__.py
│   ├── transcriber.py              # Audio transcription
│   ├── parser.py                   # NLP parsing
│   ├── formatter.py                # Minutes formatting
│   ├── exporter.py                 # Document export
│   ├── comparator.py               # Document comparison
│   └── user_profiles.py            # User preferences
└── README.md                       # This file
```

## 🚀 Quick Start

### Prerequisites

1. Python 3.8 or higher
2. pip package manager

### Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
python run.py
```

The server will start on `http://localhost:5000`

### Admin Setup

Create an admin user account:
```bash
# Using the simple creation script
python3 create_user.py create admin admin@example.com password123 "Admin" "User"

# Using the advanced CLI tool
python3 admin_cli.py create admin admin@example.com --password password123 --admin

# List all users
python3 create_user.py list
```

### Testing

Run the test suite to verify everything is working:
```bash
python test_app.py
```

## 📡 API Endpoints

### Health Check
```
GET /
GET /api/health
```
Returns API status and configuration information.

### Authentication Endpoints

#### User Registration
```
POST /api/auth/register
```
Register a new user account.

#### User Login
```
POST /api/auth/login
```
Authenticate user and create session.

#### User Logout
```
POST /api/auth/logout
```
End user session.

#### Check Authentication
```
GET /api/auth/check
```
Verify current authentication status.

#### Password Reset Request
```
POST /api/auth/request-password-reset
```
Request a password reset token.

#### Password Reset
```
POST /api/auth/reset-password
```
Reset password using a valid token.

### File Upload
```
POST /api/upload
```
Upload an audio or video file for processing.

**Request:**
- Content-Type: `multipart/form-data`
- Body: File field named `file`

**Response:**
```json
{
  "success": true,
  "message": "File uploaded successfully",
  "data": {
    "job_id": "job_20250114_123456_abcd1234",
    "filename": "meeting.mp3",
    "file_size": "15.2MB",
    "status": "uploaded",
    "next_step": "transcription"
  }
}
```

### Job Status
```
GET /api/status/<job_id>
```
Get the current processing status of a job.

**Response:**
```json
{
  "success": true,
  "message": "Job status retrieved",
  "data": {
    "job_id": "job_20250114_123456_abcd1234",
    "filename": "meeting.mp3",
    "status": "transcribing",
    "stage": "transcription",
    "progress": 45,
    "message": "Transcribing audio...",
    "created_at": "2025-01-14T12:34:56",
    "updated_at": "2025-01-14T12:35:30"
  }
}
```

### Download Result
```
GET /api/download/<job_id>
```
Download the generated meeting minutes (DOCX file).

### List Jobs
```
GET /api/jobs
```
List all jobs (for debugging/admin purposes).

## 🔧 Configuration

Configuration is managed through environment variables and the `config.py` file:

### Core Settings
- `FLASK_ENV`: Environment (development/production/testing)
- `SECRET_KEY`: Flask secret key (required for production)
- `DATABASE_URL`: Database connection string (SQLite default)

### AI Processing
- `OPENAI_API_KEY`: OpenAI API key for transcription and processing
- `WHISPER_MODEL`: Whisper model size (tiny/base/small/medium/large)
- `OPENAI_MODEL`: GPT model for processing (gpt-4, gpt-3.5-turbo)

### Security
- `JWT_SECRET_KEY`: JWT token signing key
- `JWT_ACCESS_TOKEN_EXPIRES`: Access token expiration time
- `BCRYPT_LOG_ROUNDS`: Password hashing rounds

### Logging
- `LOG_LEVEL`: Logging level (DEBUG/INFO/WARNING/ERROR)
- `LOG_FILE`: Log file path (optional)

### File Handling
- `MAX_CONTENT_LENGTH`: Maximum file upload size
- `UPLOAD_FOLDER`: File upload directory
- `OUTPUT_FOLDER`: Generated files directory

## 📁 File Handling

### Supported Formats

**Audio:**
- MP3, WAV, FLAC, M4A, AAC, OGG, WMA

**Video:**
- MP4, AVI, MOV, MKV, WMV, FLV, WebM

### File Limits

- Maximum file size: 500MB
- Files are validated using both extension and MIME type checking
- Uploaded files are stored in the `uploads/` directory
- Generated files are stored in the `output/` directory

## 🔒 Security Features

### Authentication & Authorization
- **Secure Password Hashing**: Werkzeug pbkdf2:sha256 with salt
- **Session Management**: Flask-Login with secure session handling
- **JWT Tokens**: For API authentication and authorization
- **Password Reset**: Secure token-based password reset system
- **Rate Limiting**: Protection against brute force attacks

### Input Validation & Security
- **File Type Validation**: Using python-magic for MIME type checking
- **Input Sanitization**: Comprehensive input validation and sanitization
- **SQL Injection Protection**: SQLAlchemy ORM with parameterized queries
- **XSS Protection**: Input escaping and Content Security Policy
- **CSRF Protection**: Cross-site request forgery protection

### File Security
- **Secure Filename Generation**: UUID-based file naming
- **File Size Limits**: Configurable upload size restrictions
- **File Type Restrictions**: Whitelist-based file type validation
- **Secure File Storage**: Isolated upload and processing directories

### Network Security
- **CORS Configuration**: Proper cross-origin resource sharing setup
- **HTTPS Support**: SSL/TLS encryption support
- **Security Headers**: Comprehensive security headers implementation
- **Request Size Limits**: Protection against large request attacks

## 📊 Job Tracking

The application includes a thread-safe in-memory job tracking system:

- Jobs are tracked from upload to completion
- Status updates include progress percentages
- Automatic cleanup of old jobs
- Error handling and reporting

## 🐛 Debugging

### Logs
Application logs are written to the console and can be configured to write to files.

### Test Endpoints
- Use `test_app.py` to verify API functionality
- The `/api/jobs` endpoint shows all current jobs
- Health check endpoint provides system status

## 👥 Admin Tools

### Web Admin Panel
Access the admin interface at `/frontend/admin.html`:
- **User Management**: Create, edit, delete users
- **System Monitoring**: Health checks and performance metrics
- **Audit Logs**: System activity and security monitoring
- **Responsive Design**: Works on desktop, tablet, and mobile

### Command Line Tools

#### User Creation Script (`create_user.py`)
```bash
# Create user
python3 create_user.py create username email password "First" "Last"

# List users
python3 create_user.py list

# Reset password
python3 create_user.py reset username newpassword
```

#### Advanced Admin CLI (`admin_cli.py`)
```bash
# Create admin user
python3 admin_cli.py create admin admin@example.com --admin

# List users with details
python3 admin_cli.py list

# Interactive password reset
python3 admin_cli.py reset-password username
```

## 🔄 Development Status

### Implemented Features ✅
- **User Authentication**: Complete login/logout system
- **Admin System**: Web panel and CLI tools
- **Database Models**: SQLAlchemy models for all entities
- **API Endpoints**: RESTful API with comprehensive endpoints
- **Security**: Enterprise-grade security features
- **File Handling**: Upload and processing infrastructure
- **Template System**: Meeting template management
- **Batch Processing**: Multi-file processing capabilities
- **Calendar Integration**: Calendar sync infrastructure

### In Development 🚧
- **AI Transcription**: OpenAI Whisper integration
- **Minutes Generation**: GPT-4 powered minutes creation
- **Document Export**: Advanced DOCX generation
- **Learning System**: User preference learning
- **Email Integration**: SMTP email notifications

## 🤝 Development

To add new features:

1. Create new modules in the `modules/` directory
2. Update the job tracker with new status types
3. Add new API endpoints in `app.py`
4. Update tests in `test_app.py`
5. Document changes in this README
