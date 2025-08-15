# 🤝 Contributing to MinuteMate

Thank you for your interest in contributing to MinuteMate! This guide will help you get started with contributing to our AI-powered meeting management platform.

## 📋 **Table of Contents**
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Contributing Guidelines](#contributing-guidelines)
- [Code Standards](#code-standards)
- [Testing](#testing)
- [Documentation](#documentation)
- [Community](#community)

---

## 🚀 **Getting Started**

### **Ways to Contribute**
- 🐛 **Bug Reports** - Help us identify and fix issues
- 💡 **Feature Requests** - Suggest new functionality
- 🔧 **Code Contributions** - Submit pull requests
- 📖 **Documentation** - Improve guides and tutorials
- 🎨 **Templates** - Create meeting templates
- 🌍 **Translations** - Add language support
- 🧪 **Testing** - Help test new features

### **Before You Start**
1. **Read the Code of Conduct** - Be respectful and inclusive
2. **Check existing issues** - Avoid duplicate work
3. **Join our Discord** - Connect with the community
4. **Review the roadmap** - Understand project direction

---

## 🛠️ **Development Setup**

### **Prerequisites**
```bash
# Required software
- Python 3.8+
- Node.js 16+ (for frontend development)
- Git
- Docker (optional, for containerized development)

# Recommended tools
- VS Code with Python extension
- Postman for API testing
- Redis for local caching
```

### **Local Development**

#### **1. Fork and Clone**
```bash
# Fork the repository on GitHub
# Then clone your fork
git clone https://github.com/yourusername/minute-mate.git
cd minute-mate

# Add upstream remote
git remote add upstream https://github.com/oldgraybuzzard/minute-mate.git
```

#### **2. Environment Setup**
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration
```

#### **3. Database Setup**
```bash
# Initialize database
cd backend
python -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all()"

# Run migrations (if any)
flask db upgrade
```

#### **4. Run Development Server**
```bash
# Start the application
cd backend
python run.py

# Application will be available at:
# - Frontend: http://localhost:8080/frontend/
# - API: http://localhost:8080/api/
```

### **Docker Development (Optional)**
```bash
# Build and run with Docker Compose
docker-compose up --build

# Run tests in container
docker-compose exec app pytest

# Access container shell
docker-compose exec app bash
```

---

## 📝 **Contributing Guidelines**

### **Issue Guidelines**

#### **Bug Reports**
Use the bug report template and include:
```markdown
**Bug Description**
Clear description of the issue

**Steps to Reproduce**
1. Go to '...'
2. Click on '...'
3. See error

**Expected Behavior**
What should happen

**Actual Behavior**
What actually happens

**Environment**
- OS: [e.g., macOS 12.0]
- Browser: [e.g., Chrome 96]
- MinuteMate Version: [e.g., 1.2.0]

**Additional Context**
Screenshots, logs, etc.
```

#### **Feature Requests**
Use the feature request template:
```markdown
**Feature Description**
Clear description of the proposed feature

**Use Case**
Why is this feature needed?

**Proposed Solution**
How should this feature work?

**Alternatives Considered**
Other approaches you've considered

**Additional Context**
Mockups, examples, etc.
```

### **Pull Request Guidelines**

#### **Before Submitting**
- ✅ Create an issue first (for significant changes)
- ✅ Fork the repository
- ✅ Create a feature branch
- ✅ Write tests for your changes
- ✅ Update documentation
- ✅ Follow code style guidelines

#### **PR Template**
```markdown
**Description**
Brief description of changes

**Related Issue**
Fixes #123

**Type of Change**
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

**Testing**
- [ ] Tests pass locally
- [ ] Added new tests
- [ ] Manual testing completed

**Checklist**
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No breaking changes (or documented)
```

### **Branch Naming**
```bash
# Feature branches
feature/add-calendar-integration
feature/improve-transcription-accuracy

# Bug fix branches
bugfix/fix-upload-error
bugfix/resolve-memory-leak

# Documentation branches
docs/update-api-reference
docs/add-deployment-guide

# Hotfix branches
hotfix/security-patch
hotfix/critical-bug-fix
```

---

## 🎨 **Code Standards**

### **Python Code Style**

#### **Formatting**
```python
# Use Black for code formatting
black backend/

# Use isort for import sorting
isort backend/

# Use flake8 for linting
flake8 backend/
```

#### **Code Structure**
```python
"""Module docstring describing the module purpose."""

import os
import sys
from typing import Dict, List, Optional

from flask import Flask, request
from sqlalchemy import Column, Integer, String

from .models import User
from .utils import validate_input


class MeetingProcessor:
    """Class for processing meeting recordings.
    
    This class handles the transcription and analysis of meeting
    recordings to generate structured minutes.
    """
    
    def __init__(self, config: Dict[str, str]) -> None:
        """Initialize the meeting processor.
        
        Args:
            config: Configuration dictionary containing API keys and settings.
        """
        self.config = config
        self.transcriber = self._initialize_transcriber()
    
    def process_meeting(self, audio_file: str, template_id: str) -> Dict[str, str]:
        """Process a meeting recording.
        
        Args:
            audio_file: Path to the audio file.
            template_id: ID of the template to use.
            
        Returns:
            Dictionary containing the processed meeting data.
            
        Raises:
            ProcessingError: If the audio file cannot be processed.
        """
        # Implementation here
        pass
```

#### **Error Handling**
```python
# Use specific exception types
class MinuteMateError(Exception):
    """Base exception for MinuteMate."""
    pass

class TranscriptionError(MinuteMateError):
    """Error during transcription process."""
    pass

class TemplateError(MinuteMateError):
    """Error with template processing."""
    pass

# Proper error handling
try:
    result = process_audio(audio_file)
except TranscriptionError as e:
    logger.error(f"Transcription failed: {e}")
    raise
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    raise MinuteMateError(f"Processing failed: {e}")
```

### **JavaScript Code Style**

#### **Modern JavaScript**
```javascript
// Use ES6+ features
const processUpload = async (file) => {
    try {
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error(`Upload failed: ${response.statusText}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('Upload error:', error);
        throw error;
    }
};

// Use proper event handling
document.addEventListener('DOMContentLoaded', () => {
    const uploadButton = document.getElementById('upload-btn');
    uploadButton?.addEventListener('click', handleUpload);
});
```

### **Database Migrations**
```python
# Create migration
flask db migrate -m "Add user preferences table"

# Review migration file
# Edit if necessary

# Apply migration
flask db upgrade
```

---

## 🧪 **Testing**

### **Test Structure**
```
tests/
├── unit/                   # Unit tests
│   ├── test_models.py
│   ├── test_services.py
│   └── test_utils.py
├── integration/            # Integration tests
│   ├── test_api.py
│   └── test_database.py
├── e2e/                   # End-to-end tests
│   └── test_workflows.py
└── fixtures/              # Test data
    ├── audio_samples/
    └── templates/
```

### **Writing Tests**

#### **Unit Tests**
```python
import pytest
from unittest.mock import Mock, patch

from backend.services.transcription import TranscriptionService
from backend.models import Meeting


class TestTranscriptionService:
    """Test cases for TranscriptionService."""
    
    @pytest.fixture
    def service(self):
        """Create a TranscriptionService instance for testing."""
        config = {'openai_api_key': 'test-key'}
        return TranscriptionService(config)
    
    @patch('backend.services.transcription.openai')
    def test_transcribe_audio_success(self, mock_openai, service):
        """Test successful audio transcription."""
        # Arrange
        mock_openai.Audio.transcribe.return_value = {
            'text': 'Test transcription'
        }
        audio_file = 'test.mp3'
        
        # Act
        result = service.transcribe_audio(audio_file)
        
        # Assert
        assert result == 'Test transcription'
        mock_openai.Audio.transcribe.assert_called_once()
    
    def test_transcribe_audio_invalid_file(self, service):
        """Test transcription with invalid file."""
        with pytest.raises(FileNotFoundError):
            service.transcribe_audio('nonexistent.mp3')
```

#### **Integration Tests**
```python
import pytest
from flask import url_for

from backend.app import create_app, db
from backend.models import User, Meeting


@pytest.fixture
def app():
    """Create application for testing."""
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def authenticated_user(client):
    """Create and authenticate a test user."""
    user_data = {
        'email': 'test@example.com',
        'password': 'testpass123',
        'username': 'testuser'
    }
    
    # Register user
    client.post('/api/auth/register', json=user_data)
    
    # Login user
    response = client.post('/api/auth/login', json={
        'email': user_data['email'],
        'password': user_data['password']
    })
    
    return response.json['data']['user']


def test_create_meeting(client, authenticated_user):
    """Test meeting creation via API."""
    meeting_data = {
        'title': 'Test Meeting',
        'description': 'Test meeting description'
    }
    
    response = client.post('/api/meetings', json=meeting_data)
    
    assert response.status_code == 201
    assert response.json['success'] is True
    assert 'meeting' in response.json['data']
```

### **Running Tests**
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_models.py

# Run with coverage
pytest --cov=backend --cov-report=html

# Run tests in parallel
pytest -n auto

# Run only failed tests
pytest --lf
```

---

## 📖 **Documentation**

### **Documentation Types**
- **API Documentation** - Endpoint specifications
- **User Guides** - How-to instructions
- **Developer Docs** - Technical implementation details
- **Code Comments** - Inline documentation
- **README Updates** - Project overview changes

### **Writing Guidelines**

#### **API Documentation**
```python
@app.route('/api/meetings', methods=['POST'])
def create_meeting():
    """Create a new meeting.
    
    Creates a new meeting record and initiates processing of the
    uploaded audio/video file.
    
    Request Body:
        title (str): Meeting title
        description (str, optional): Meeting description
        template_id (str, optional): Template to use for minutes
        file (file): Audio/video file to process
    
    Returns:
        201: Meeting created successfully
        400: Invalid request data
        413: File too large
        
    Example:
        >>> response = client.post('/api/meetings', 
        ...     data={'title': 'Board Meeting'},
        ...     files={'file': open('meeting.mp3', 'rb')})
        >>> print(response.json)
        {
            "success": true,
            "data": {
                "meeting": {
                    "id": "meeting-uuid",
                    "title": "Board Meeting",
                    "status": "processing"
                }
            }
        }
    """
    # Implementation here
    pass
```

#### **User Documentation**
```markdown
# How to Upload a Meeting Recording

Follow these steps to upload and process a meeting recording:

## Step 1: Prepare Your File
- Supported formats: MP3, WAV, MP4, AVI, MOV
- Maximum file size: 100MB
- Recommended: Clear audio with minimal background noise

## Step 2: Upload the File
1. Navigate to the **Meetings** page
2. Click the **Upload Recording** button
3. Select your audio/video file
4. Fill in the meeting details:
   - **Title**: Give your meeting a descriptive name
   - **Description**: Add any relevant context
   - **Template**: Choose a template (optional)

## Step 3: Monitor Processing
- Processing typically takes 2-5 minutes
- You'll see a progress indicator
- You'll receive an email when processing is complete

## Step 4: Review and Download
- Review the generated minutes
- Make any necessary edits
- Download in your preferred format (DOCX, HTML, JSON)
```

---

## 🌟 **Community**

### **Communication Channels**
- 💬 **Discord**: [Join our community](https://discord.gg/minutemate)
- 📧 **Email**: contribute@minutemate.com
- 🐛 **Issues**: [GitHub Issues](https://github.com/oldgraybuzzard/minute-mate/issues)
- 💡 **Discussions**: [GitHub Discussions](https://github.com/oldgraybuzzard/minute-mate/discussions)

### **Code of Conduct**
We are committed to providing a welcoming and inclusive environment. Please read our [Code of Conduct](CODE_OF_CONDUCT.md) before participating.

### **Recognition**
Contributors are recognized in:
- 📜 **Contributors file** - Listed in CONTRIBUTORS.md
- 🏆 **Release notes** - Mentioned in changelog
- 🎉 **Community highlights** - Featured in newsletters
- 🎁 **Swag** - MinuteMate merchandise for significant contributions

---

## 🎯 **Getting Help**

### **Development Questions**
- 📖 Check the [documentation](https://docs.minutemate.com)
- 🔍 Search existing [issues](https://github.com/oldgraybuzzard/minute-mate/issues)
- 💬 Ask in [Discord](https://discord.gg/minutemate)
- 📧 Email: dev-help@minutemate.com

### **Mentorship Program**
New contributors can request mentorship:
- 👥 **Pair programming** sessions
- 📚 **Code review** guidance
- 🎯 **Issue assignment** help
- 🚀 **Career development** advice

---

## 🙏 **Thank You**

Thank you for contributing to MinuteMate! Your contributions help make meeting management more efficient for teams worldwide.

**Happy coding!** 🚀
