# 🔧 MinuteMate Configuration Guide

Complete guide to configuring MinuteMate for different environments and use cases.

## 📋 **Table of Contents**
- [Environment Variables](#environment-variables)
- [Database Configuration](#database-configuration)
- [AI Model Settings](#ai-model-settings)
- [Security Configuration](#security-configuration)
- [File Upload Settings](#file-upload-settings)
- [Performance Tuning](#performance-tuning)
- [Integration Settings](#integration-settings)

---

## 🌍 **Environment Variables**

### **Required Settings**
```bash
# OpenAI API Key (Required for AI features)
OPENAI_API_KEY=your-openai-api-key-here
```

### **Database Settings**
```bash
# Database URL (Auto-provided by Railway)
DATABASE_URL=postgresql://user:password@host:port/database

# SQLite fallback for local development
# DATABASE_URL=sqlite:///minutemate.db
```

### **Security Settings**
```bash
# Secret key for sessions and encryption
SECRET_KEY=your-secure-secret-key-here

# Flask environment
FLASK_ENV=production                 # production, development, testing

# Redis for caching and rate limiting
REDIS_URL=redis://localhost:6379/0
```

### **AI Model Configuration**
```bash
# Whisper model for transcription
WHISPER_MODEL=base                   # tiny, base, small, medium, large

# OpenAI model for minutes generation
OPENAI_MODEL=gpt-4                   # gpt-4, gpt-3.5-turbo

# Processing timeout (seconds)
MAX_PROCESSING_TIME=3600             # 1 hour default
```

### **File Upload Limits**
```bash
# Maximum request size (bytes)
MAX_CONTENT_LENGTH=104857600         # 100MB

# Audio file size limit
MAX_AUDIO_SIZE=524288000             # 500MB

# Video file size limit
MAX_VIDEO_SIZE=2147483648            # 2GB

# Document file size limit
MAX_DOCUMENT_SIZE=52428800           # 50MB
```

### **Performance Settings**
```bash
# Database connection pool
DB_POOL_SIZE=10
DB_POOL_TIMEOUT=20
DB_POOL_RECYCLE=3600
DB_MAX_OVERFLOW=20

# Cache timeout (seconds)
CACHE_TIMEOUT=3600                   # 1 hour

# Rate limiting
RATELIMIT_DEFAULT=100/hour
```

### **Email Configuration (Optional)**
```bash
# SMTP settings for notifications
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=your-email@gmail.com
```

### **Calendar Integration (Optional)**
```bash
# Google Calendar
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# Microsoft Calendar
MICROSOFT_CLIENT_ID=your-microsoft-client-id
MICROSOFT_CLIENT_SECRET=your-microsoft-client-secret
```

---

## 🗄️ **Database Configuration**

### **PostgreSQL (Recommended for Production)**
```bash
# Railway automatically provides this
DATABASE_URL=postgresql://user:password@host:port/database

# Manual configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=minutemate
DB_USER=minutemate_user
DB_PASSWORD=secure_password
```

### **SQLite (Development Only)**
```bash
# Local development
DATABASE_URL=sqlite:///minutemate.db

# In-memory for testing
DATABASE_URL=sqlite:///:memory:
```

### **Database Pool Settings**
```bash
# Connection pool configuration
SQLALCHEMY_POOL_SIZE=10              # Number of connections to maintain
SQLALCHEMY_POOL_TIMEOUT=20           # Seconds to wait for connection
SQLALCHEMY_POOL_RECYCLE=3600         # Seconds before recreating connection
SQLALCHEMY_MAX_OVERFLOW=20           # Additional connections beyond pool_size
```

---

## 🤖 **AI Model Settings**

### **Whisper Models**
| Model | Size | Speed | Accuracy | Use Case |
|-------|------|-------|----------|----------|
| `tiny` | 39 MB | Fastest | Good | Quick testing |
| `base` | 74 MB | Fast | Better | Development |
| `small` | 244 MB | Medium | Good | Production |
| `medium` | 769 MB | Slow | Better | High accuracy |
| `large` | 1550 MB | Slowest | Best | Maximum accuracy |

### **OpenAI Models**
| Model | Cost | Speed | Quality | Use Case |
|-------|------|-------|---------|----------|
| `gpt-3.5-turbo` | Low | Fast | Good | Cost-effective |
| `gpt-4` | High | Slow | Excellent | Best quality |
| `gpt-4-turbo` | Medium | Medium | Excellent | Balanced |

### **Model Configuration**
```bash
# Whisper settings
WHISPER_MODEL=base
WHISPER_DEVICE=cpu                   # cpu, cuda
WHISPER_LANGUAGE=auto                # auto, en, es, fr, etc.

# OpenAI settings
OPENAI_MODEL=gpt-4
OPENAI_TEMPERATURE=0.3               # 0.0-1.0, lower = more consistent
OPENAI_MAX_TOKENS=4000               # Maximum response length
```

---

## 🔒 **Security Configuration**

### **Rate Limiting**
```bash
# Global rate limits
RATELIMIT_DEFAULT=100/hour

# Endpoint-specific limits
AUTH_RATE_LIMIT=5/5minutes           # Login attempts
UPLOAD_RATE_LIMIT=10/hour            # File uploads
API_RATE_LIMIT=1000/hour             # API requests
```

### **Session Security**
```bash
# Session configuration
SESSION_COOKIE_SECURE=true           # HTTPS only
SESSION_COOKIE_HTTPONLY=true         # No JavaScript access
SESSION_COOKIE_SAMESITE=Strict       # CSRF protection
PERMANENT_SESSION_LIFETIME=86400     # 24 hours
```

### **Content Security Policy**
```bash
# CSP settings (automatically configured)
CSP_DEFAULT_SRC=self
CSP_SCRIPT_SRC=self,unsafe-inline,cdnjs.cloudflare.com
CSP_STYLE_SRC=self,unsafe-inline,cdnjs.cloudflare.com
```

---

## 📁 **File Upload Settings**

### **Allowed File Types**
```bash
# Audio formats
ALLOWED_AUDIO_EXTENSIONS=mp3,wav,flac,m4a,aac,ogg

# Video formats
ALLOWED_VIDEO_EXTENSIONS=mp4,avi,mov,mkv,webm

# Document formats
ALLOWED_DOCUMENT_EXTENSIONS=docx,doc
```

### **Storage Configuration**
```bash
# Upload directories
UPLOAD_FOLDER=../uploads
OUTPUT_FOLDER=../output
TEMP_FOLDER=../temp

# File retention (days)
TEMP_FILE_RETENTION=7
OUTPUT_FILE_RETENTION=30
```

---

## ⚡ **Performance Tuning**

### **Caching Configuration**
```bash
# Cache backend
CACHE_TYPE=redis                     # redis, simple, null
CACHE_REDIS_URL=redis://localhost:6379/0
CACHE_DEFAULT_TIMEOUT=3600

# Cache keys
CACHE_KEY_PREFIX=minutemate:
```

### **Background Jobs**
```bash
# Celery configuration
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
CELERY_TASK_SERIALIZER=json
CELERY_RESULT_SERIALIZER=json
```

### **Logging Configuration**
```bash
# Log levels
LOG_LEVEL=INFO                       # DEBUG, INFO, WARNING, ERROR

# Log files
LOG_FILE=/var/log/minutemate.log
LOG_MAX_BYTES=10485760               # 10MB
LOG_BACKUP_COUNT=5
```

---

## 🔗 **Integration Settings**

### **Calendar Providers**
```bash
# Google Calendar OAuth
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REDIRECT_URI=https://your-app.com/auth/google/callback

# Microsoft Calendar OAuth
MICROSOFT_CLIENT_ID=your-client-id
MICROSOFT_CLIENT_SECRET=your-client-secret
MICROSOFT_REDIRECT_URI=https://your-app.com/auth/microsoft/callback
```

### **External Services**
```bash
# Webhook URLs for notifications
WEBHOOK_URL=https://your-webhook-endpoint.com
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
TEAMS_WEBHOOK_URL=https://outlook.office.com/webhook/...
```

---

## 🚀 **Environment-Specific Configurations**

### **Development**
```bash
FLASK_ENV=development
DEBUG=true
SQLALCHEMY_ECHO=true
LOG_LEVEL=DEBUG
CACHE_TYPE=simple
```

### **Staging**
```bash
FLASK_ENV=staging
DEBUG=false
LOG_LEVEL=INFO
CACHE_TYPE=redis
RATELIMIT_DEFAULT=200/hour
```

### **Production**
```bash
FLASK_ENV=production
DEBUG=false
LOG_LEVEL=WARNING
CACHE_TYPE=redis
SESSION_COOKIE_SECURE=true
RATELIMIT_DEFAULT=100/hour
```

---

## 🔍 **Configuration Validation**

MinuteMate automatically validates configuration on startup:

### **Required Checks**
- ✅ OpenAI API key is set
- ✅ Database connection is valid
- ✅ Upload directories are writable
- ✅ Secret key is secure (production)

### **Optional Warnings**
- ⚠️ Redis not available (falls back to simple cache)
- ⚠️ Email not configured (notifications disabled)
- ⚠️ Calendar integration not set up

### **Health Check Endpoint**
Visit `/api/health` to see configuration status:
```json
{
  "status": "healthy",
  "checks": {
    "database": {"status": "healthy"},
    "redis": {"status": "healthy"},
    "filesystem": {"status": "healthy"},
    "ai_service": {"status": "configured"}
  }
}
```

---

## 🛠️ **Troubleshooting**

### **Common Issues**

**Database Connection Failed**
```bash
# Check DATABASE_URL format
DATABASE_URL=postgresql://user:password@host:port/database

# Verify credentials and network access
```

**OpenAI API Errors**
```bash
# Verify API key
OPENAI_API_KEY=sk-...

# Check API quota and billing
```

**File Upload Issues**
```bash
# Check file size limits
MAX_CONTENT_LENGTH=104857600

# Verify upload directory permissions
chmod 755 uploads/
```

**Redis Connection Failed**
```bash
# Check Redis URL
REDIS_URL=redis://localhost:6379/0

# Verify Redis server is running
redis-cli ping
```

---

## 📞 **Support**

For configuration help:
- 📧 Email: support@minutemate.com
- 📖 Documentation: [docs.minutemate.com](https://docs.minutemate.com)
- 🐛 Issues: [GitHub Issues](https://github.com/yourusername/minute-mate/issues)
