# MinuteMate Backend

The MinuteMate backend is a Flask-based API server that handles file uploads, processing, and serves the generated meeting minutes.

## 🏗️ Architecture

```
backend/
├── app.py              # Main Flask application
├── config.py           # Configuration management
├── utils.py            # Utility functions
├── job_tracker.py      # Job status tracking
├── modules/            # Processing modules
│   ├── __init__.py
│   ├── transcriber.py  # Audio transcription (to be implemented)
│   ├── parser.py       # NLP parsing (to be implemented)
│   ├── formatter.py    # Minutes formatting (to be implemented)
│   ├── exporter.py     # DOCX export (to be implemented)
│   ├── comparator.py   # Document comparison (to be implemented)
│   └── user_profiles.py # User preferences (to be implemented)
└── README.md           # This file
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

### Testing

Run the test suite to verify everything is working:
```bash
python test_app.py
```

## 📡 API Endpoints

### Health Check
```
GET /
```
Returns API status and configuration information.

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

- `FLASK_ENV`: Environment (development/production/testing)
- `SECRET_KEY`: Flask secret key (required for production)
- `WHISPER_MODEL`: Whisper model size (tiny/base/small/medium/large)
- `LOG_LEVEL`: Logging level (DEBUG/INFO/WARNING/ERROR)

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

- File type validation using python-magic
- Secure filename generation
- File size limits
- CORS support for frontend integration
- Request entity size limits

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

## 🔄 Next Steps

The following modules need to be implemented:

1. **transcriber.py** - Whisper integration for audio transcription
2. **parser.py** - NLP parsing for extracting meeting structure
3. **formatter.py** - Robert's Rules formatting
4. **exporter.py** - DOCX document generation
5. **comparator.py** - Document comparison for learning
6. **user_profiles.py** - User preference management

## 🤝 Development

To add new features:

1. Create new modules in the `modules/` directory
2. Update the job tracker with new status types
3. Add new API endpoints in `app.py`
4. Update tests in `test_app.py`
5. Document changes in this README
