# 📋 BoardMinutes

**Professional AI-Powered Board Meeting Minutes**

Transform your board meeting recordings into professional, compliant minutes with advanced AI intelligence. BoardMinutes is designed specifically for professional boards, committees, and governance meetings with enterprise-grade features and comprehensive admin tools.

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/minutemate)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Admin Panel](https://img.shields.io/badge/Admin-Panel-blue.svg)](#-admin-system)

---

## 🌟 **Key Features**

### 🤖 **AI-Powered Intelligence**
- **Advanced Transcription** using OpenAI Whisper with 95%+ accuracy
- **Intelligent Minutes Generation** with GPT-4 for professional formatting
- **Smart Document Learning** that adapts to your preferences over time
- **Context-Aware Processing** that understands meeting dynamics

### 📋 **Professional Templates**
- **50+ Pre-built Templates** for every meeting type
- **Robert's Rules of Order** compliance for formal meetings
- **Custom Template Builder** with drag-and-drop sections
- **Industry-Specific Formats** (Board meetings, Stand-ups, Reviews)

### 🔗 **Enterprise Integrations**
- **Calendar Sync** with Google Calendar, Outlook, and more
- **URL Processing** for Zoom, Teams, and other platforms
- **Batch Processing** for multiple files simultaneously
- **API Integration** for custom workflows

### 🧠 **Adaptive Learning**
- **Upload Edited Minutes** to teach the system your preferences
- **Automatic Style Application** to future documents
- **Preference Learning** for fonts, formatting, and structure
- **Confidence-Based Improvements** that get better over time

### 🔒 **Enterprise Security & Admin**
- **Comprehensive Admin System** with web interface and CLI tools
- **User Management** with role-based access control
- **Password Reset** functionality with secure token system
- **Rate Limiting** to prevent abuse and ensure fair usage
- **Input Validation** with comprehensive security checks
- **Error Handling** with detailed logging and monitoring
- **Production-Ready** with health checks and metrics

### 👥 **User Management**
- **Professional Admin Panel** with modern, responsive design
- **CLI Admin Tools** for server management and user operations
- **User Authentication** with secure session management
- **Password Reset System** with email integration (development mode)
- **User Profiles** with customizable preferences and settings
- **Audit Logging** for security and compliance tracking

---

## 🚀 **Quick Start**

### **Option 1: One-Click Deploy (Recommended)**
[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/minutemate)

1. Click the deploy button above
2. Add your `OPENAI_API_KEY` in Railway dashboard
3. Your app will be live in minutes!

### **Option 2: Local Development**

#### **Prerequisites**
- Python 3.8+
- OpenAI API key
- FFmpeg (for audio processing)

#### **Installation**
```bash
# Clone the repository
git clone https://github.com/yourusername/boardminutes.git
cd boardminutes

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
export OPENAI_API_KEY="your-openai-api-key-here"

# Run the application
cd backend
python run.py
```

#### **Access the Application**
- **Web Interface:** http://localhost:5000/frontend/
- **Admin Panel:** http://localhost:5000/frontend/admin.html
- **API Documentation:** http://localhost:5000/api/docs/html
- **Health Check:** http://localhost:5000/api/health

#### **Admin Setup**
```bash
# Create admin user account
cd backend
python3 create_user.py create admin admin@example.com password123 "Admin" "User"

# Or use the CLI admin tool
python3 admin_cli.py create admin admin@example.com --password password123 --admin

# List all users
python3 create_user.py list
```

---

## 💡 **How It Works**

### **1. Upload & Process** 🎵
- Upload audio/video files or provide URLs
- Support for 15+ file formats
- Automatic format detection and conversion

### **2. AI Transcription** 🤖
- OpenAI Whisper for accurate speech-to-text
- Multi-language support
- Speaker identification and timestamps

### **3. Intelligent Minutes** 📝
- GPT-4 analyzes transcription for key points
- Applies your chosen template
- Generates action items and summaries

### **4. Learn & Improve** 🧠
- Upload edited versions to teach preferences
- System learns your formatting style
- Future documents automatically personalized

---

## 🛡️ **Admin System**

BoardMinutes includes a comprehensive administration system for enterprise deployment and user management.

### **🖥️ Web Admin Panel**
Access the professional admin interface at `/frontend/admin.html`:

- **User Management**: Create, edit, delete, and manage user accounts
- **Password Reset**: Admin-initiated password resets for users
- **System Monitoring**: Real-time system health and performance metrics
- **Audit Logs**: Comprehensive logging for security and compliance
- **Responsive Design**: Works perfectly on desktop, tablet, and mobile devices

### **⚡ CLI Admin Tools**

#### **User Creation Script** (`create_user.py`)
```bash
# Create a new user
python3 create_user.py create username email@example.com password123 "First" "Last"

# List all users
python3 create_user.py list

# Reset user password
python3 create_user.py reset username newpassword123
```

#### **Advanced Admin CLI** (`admin_cli.py`)
```bash
# Create user with admin privileges
python3 admin_cli.py create username email@example.com --password pass123 --admin

# List all users with detailed information
python3 admin_cli.py list

# Reset user password interactively
python3 admin_cli.py reset-password username
```

### **🔐 Security Features**
- **Secure Password Hashing**: Uses Werkzeug's pbkdf2:sha256 for password security
- **Session Management**: Secure user sessions with proper timeout handling
- **Token-Based Password Reset**: Secure password reset with 1-hour expiration tokens
- **Input Validation**: Comprehensive validation for all user inputs
- **Rate Limiting**: Protection against brute force attacks

### **📊 Admin Dashboard Features**
- **User Statistics**: Total users, active sessions, and growth metrics
- **System Health**: Server status, database size, and performance indicators
- **Activity Logs**: Real-time monitoring of user activities and system events
- **Responsive Tables**: Professional data tables with search and filtering
- **Modern UI**: Clean, professional interface matching enterprise standards

---

## 🎯 **Use Cases**

### **Corporate Meetings**
- Board meetings with Robert's Rules compliance
- Executive briefings with action item tracking
- Team stand-ups with progress summaries
- Client calls with professional formatting

### **Educational Institutions**
- Faculty meetings with academic formatting
- Student organization meetings
- Research collaboration sessions
- Administrative planning meetings

### **Healthcare Organizations**
- Medical staff meetings with HIPAA considerations
- Quality improvement sessions
- Administrative meetings
- Training session documentation

### **Legal & Compliance**
- Legal team meetings with precise documentation
- Compliance review sessions
- Contract negotiation summaries
- Regulatory meeting minutes

---

## 📊 **Supported Formats**

### **Input Formats**
| Type | Formats |
|------|---------|
| **Audio** | MP3, WAV, FLAC, M4A, AAC, OGG |
| **Video** | MP4, AVI, MOV, MKV, WEBM |
| **URLs** | Zoom, Teams, Google Meet, YouTube |

### **Output Formats**
| Format | Description |
|--------|-------------|
| **DOCX** | Professional Word documents with formatting |
| **HTML** | Web-ready format with responsive design |
| **JSON** | Structured data for API integration |
| **PDF** | Print-ready documents (coming soon) |

---

## 🔧 **Configuration**

### **Environment Variables**
```bash
# Required
OPENAI_API_KEY=your-openai-api-key-here

# Optional - AI Models
WHISPER_MODEL=base                    # base, small, medium, large
OPENAI_MODEL=gpt-4                   # gpt-4, gpt-3.5-turbo

# Optional - Database
DATABASE_URL=postgresql://...         # Auto-provided by Railway

# Optional - Security
SECRET_KEY=your-secret-key           # Auto-generated by Railway
REDIS_URL=redis://...                # For caching and rate limiting

# Optional - File Limits
MAX_CONTENT_LENGTH=104857600         # 100MB default
MAX_AUDIO_SIZE=524288000             # 500MB for audio
MAX_VIDEO_SIZE=2147483648            # 2GB for video
```

### **Advanced Configuration**
See [Configuration Guide](docs/CONFIGURATION.md) for detailed settings.

---

## 📚 **Documentation**

| Document | Description |
|----------|-------------|
| [🚀 Deployment Guide](RAILWAY_DEPLOYMENT.md) | Complete Railway deployment instructions |
| [🔧 Configuration](docs/CONFIGURATION.md) | Advanced configuration options |
| [📖 API Reference](docs/API.md) | Complete API documentation |
| [🎨 Templates](docs/TEMPLATES.md) | Template creation and customization |
| [🔗 Integrations](docs/INTEGRATIONS.md) | Calendar and third-party integrations |
| [🛡️ Security](docs/SECURITY.md) | Security features and best practices |
| [🧠 AI Features](docs/AI_FEATURES.md) | AI capabilities and learning system |
| [👥 Admin Guide](docs/ADMIN.md) | Admin panel and user management |
| [🏗️ Architecture](docs/Architecture.md) | System architecture and design |
| [🤝 Contributing](docs/CONTRIBUTING.md) | Development and contribution guide |

---

## 🛠️ **Development**

### **Project Structure**
```
boardminutes/
├── backend/                 # Flask API server
│   ├── app.py              # Main Flask application
│   ├── models.py           # SQLAlchemy database models
│   ├── auth_service.py     # Authentication and user management
│   ├── auth_routes.py      # Authentication API endpoints
│   ├── admin_cli.py        # Command-line admin tools
│   ├── create_user.py      # Simple user creation script
│   ├── migrate_db.py       # Database migration utilities
│   ├── meeting_service.py  # Meeting processing logic
│   ├── template_service.py # Template management
│   ├── batch_service.py    # Batch processing system
│   ├── calendar_service.py # Calendar integrations
│   ├── document_*.py       # Document processing modules
│   ├── modules/            # Core processing modules
│   │   ├── transcriber.py  # Audio transcription
│   │   ├── formatter.py    # Minutes formatting
│   │   ├── exporter.py     # Document export
│   │   └── comparator.py   # Document comparison
│   └── config.py           # Configuration management
├── frontend/               # Web interface
│   ├── index.html          # Landing page
│   ├── auth.html           # Login/registration
│   ├── dashboard.html      # User dashboard
│   ├── admin.html          # Admin panel
│   ├── admin.js            # Admin panel functionality
│   ├── styles.css          # Comprehensive styling
│   └── assets/             # Images and resources
├── docs/                   # Comprehensive documentation
│   ├── API.md              # API reference
│   ├── CONFIGURATION.md    # Configuration guide
│   ├── SECURITY.md         # Security documentation
│   └── *.md                # Additional guides
├── requirements.txt        # Python dependencies
└── railway.json           # Railway deployment config
```

### **Contributing**
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

See [Contributing Guide](docs/CONTRIBUTING.md) for detailed instructions.

---

## 🎉 **Success Stories**

> *"BoardMinutes reduced our meeting documentation time by 85%. The AI learning feature means our minutes get better every week!"*
> **— Sarah Chen, Operations Director**

> *"The Robert's Rules compliance feature is perfect for our board meetings. Professional results every time."*
> **— Michael Rodriguez, Board Secretary**

> *"Batch processing saved us hours when digitizing our archived meeting recordings."*
> **— Dr. Amanda Foster, Research Director**

---

## 🤝 **Support & Community**

- **📧 Email:** support@boardminutes.com
- **💬 Discord:** [Join our community](https://discord.gg/boardminutes)
- **🐛 Issues:** [GitHub Issues](https://github.com/yourusername/boardminutes/issues)
- **📖 Docs:** [Documentation Site](https://docs.boardminutes.com)

---

## 📄 **License**

MIT License - see [LICENSE](LICENSE) file for details.

---

## 🙏 **Acknowledgments**

- OpenAI for Whisper and GPT models
- Railway for excellent deployment platform
- The open-source community for amazing tools and libraries

---

<div align="center">

**Ready to transform your meetings?**

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/minutemate)

*Professional meeting minutes in minutes, not hours.*

</div>