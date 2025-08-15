# 📖 MinuteMate API Reference

Complete API documentation for MinuteMate's RESTful API.

## 📋 **Table of Contents**
- [Authentication](#authentication)
- [Meeting Management](#meeting-management)
- [Document Processing](#document-processing)
- [Template Management](#template-management)
- [Calendar Integration](#calendar-integration)
- [User Management](#user-management)
- [Batch Processing](#batch-processing)
- [Error Handling](#error-handling)

---

## 🔐 **Authentication**

MinuteMate uses session-based authentication with secure cookies.

### **Register User**
```http
POST /api/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "username": "johndoe",
  "password": "securepassword123",
  "first_name": "John",
  "last_name": "Doe"
}
```

**Response:**
```json
{
  "success": true,
  "message": "User created successfully",
  "data": {
    "user": {
      "id": "user-uuid",
      "email": "user@example.com",
      "username": "johndoe",
      "full_name": "John Doe"
    }
  }
}
```

### **Login**
```http
POST /api/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Login successful",
  "data": {
    "user": {
      "id": "user-uuid",
      "email": "user@example.com",
      "full_name": "John Doe"
    }
  }
}
```

### **Logout**
```http
POST /api/auth/logout
```

### **Check Authentication**
```http
GET /api/auth/check
```

---

## 🎙️ **Meeting Management**

### **List Meetings**
```http
GET /api/meetings?page=1&per_page=10&status=completed&search=board
```

**Parameters:**
- `page` (int): Page number (default: 1)
- `per_page` (int): Items per page (default: 10, max: 100)
- `status` (string): Filter by status (pending, processing, completed, failed)
- `search` (string): Search in title and description

**Response:**
```json
{
  "success": true,
  "data": {
    "meetings": [
      {
        "id": "meeting-uuid",
        "title": "Board Meeting Q4",
        "description": "Quarterly board meeting",
        "status": "completed",
        "meeting_date": "2024-01-15T14:00:00Z",
        "duration_minutes": 90,
        "original_filename": "board_meeting.mp3",
        "has_edited_version": true,
        "created_at": "2024-01-15T13:00:00Z"
      }
    ],
    "total": 25,
    "page": 1,
    "per_page": 10,
    "pages": 3
  }
}
```

### **Create Meeting**
```http
POST /api/meetings
Content-Type: multipart/form-data

file: [audio/video file]
title: "Board Meeting Q4"
description: "Quarterly board meeting"
template_id: "template-uuid"
meeting_date: "2024-01-15T14:00:00Z"
```

**Response:**
```json
{
  "success": true,
  "message": "Meeting created and processing started",
  "data": {
    "meeting": {
      "id": "meeting-uuid",
      "title": "Board Meeting Q4",
      "status": "processing",
      "job_id": "job-uuid"
    }
  }
}
```

### **Get Meeting Details**
```http
GET /api/meetings/{meeting_id}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "meeting": {
      "id": "meeting-uuid",
      "title": "Board Meeting Q4",
      "description": "Quarterly board meeting",
      "status": "completed",
      "meeting_date": "2024-01-15T14:00:00Z",
      "duration_minutes": 90,
      "summary": "Meeting summary...",
      "action_items": [
        {
          "item": "Review budget proposal",
          "assignee": "John Doe",
          "due_date": "2024-01-30"
        }
      ],
      "participants": ["John Doe", "Jane Smith"],
      "template_id": "template-uuid",
      "has_edited_version": true
    }
  }
}
```

### **Update Meeting**
```http
PUT /api/meetings/{meeting_id}
Content-Type: application/json

{
  "title": "Updated Meeting Title",
  "description": "Updated description",
  "meeting_date": "2024-01-15T14:00:00Z"
}
```

### **Delete Meeting**
```http
DELETE /api/meetings/{meeting_id}
```

### **Download Meeting Document**
```http
GET /api/meetings/{meeting_id}/download?format=docx
```

**Parameters:**
- `format` (string): Output format (docx, html, json)

---

## 📄 **Document Processing**

### **Upload Edited Document**
```http
POST /api/documents/upload-edited/{meeting_id}
Content-Type: multipart/form-data

file: [edited DOCX file]
```

**Response:**
```json
{
  "success": true,
  "message": "Document uploaded and preferences learned successfully",
  "data": {
    "meeting_id": "meeting-uuid",
    "comparison_summary": {
      "preferences_learned": 5,
      "confidence_score": 0.85,
      "content_changes": 12,
      "formatting_changes": 8
    }
  }
}
```

### **Get Comparison Results**
```http
GET /api/documents/comparison/{meeting_id}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "meeting_id": "meeting-uuid",
    "comparison_data": {
      "learned_preferences": {
        "preferred_font": "Arial",
        "preferred_font_size": 12,
        "preferred_alignment": "left"
      },
      "text_changes": {
        "word_count_change": 150,
        "additions": ["New section added"],
        "deletions": ["Removed redundant text"]
      },
      "formatting_changes": {
        "fonts_changes": {"changed": true},
        "sizes_changes": {"changed": false}
      }
    }
  }
}
```

### **Get User Preferences**
```http
GET /api/documents/preferences
```

**Response:**
```json
{
  "success": true,
  "data": {
    "preferences": {
      "formatting": {
        "preferred_font": {
          "value": "Arial",
          "confidence": 0.9,
          "category": "learned_from_edit"
        }
      },
      "content": {
        "prefers_detailed_content": {
          "value": true,
          "confidence": 0.8,
          "category": "learned_from_edit"
        }
      }
    },
    "total_preferences": 12,
    "categories": ["formatting", "content", "structure"]
  }
}
```

### **Apply Preferences to Document**
```http
POST /api/documents/apply-preferences/{meeting_id}
```

### **Download Personalized Document**
```http
GET /api/documents/download-personalized/{meeting_id}
```

---

## 📋 **Template Management**

### **List Templates**
```http
GET /api/templates?category=board_meeting&public=true
```

**Parameters:**
- `category` (string): Filter by category
- `public` (boolean): Include public templates

**Response:**
```json
{
  "success": true,
  "data": {
    "templates": [
      {
        "id": "template-uuid",
        "name": "Board Meeting Template",
        "description": "Standard board meeting format",
        "category": "board_meeting",
        "is_public": true,
        "usage_count": 150,
        "sections": [
          {
            "name": "Call to Order",
            "type": "text",
            "required": true
          },
          {
            "name": "Approval of Minutes",
            "type": "text",
            "required": true
          }
        ]
      }
    ]
  }
}
```

### **Create Template**
```http
POST /api/templates
Content-Type: application/json

{
  "name": "Custom Meeting Template",
  "description": "My custom template",
  "category": "general",
  "sections": [
    {
      "name": "Opening",
      "type": "text",
      "required": true,
      "prompt": "Meeting opening and attendance"
    }
  ],
  "formatting_options": {
    "font_family": "Arial",
    "font_size": 12,
    "line_spacing": 1.5
  }
}
```

### **Update Template**
```http
PUT /api/templates/{template_id}
```

### **Delete Template**
```http
DELETE /api/templates/{template_id}
```

---

## 📅 **Calendar Integration**

### **List Calendar Integrations**
```http
GET /api/calendar/integrations
```

**Response:**
```json
{
  "success": true,
  "data": {
    "integrations": [
      {
        "id": "integration-uuid",
        "provider": "google",
        "provider_email": "user@gmail.com",
        "is_active": true,
        "sync_enabled": true,
        "last_sync_at": "2024-01-15T10:00:00Z",
        "sync_status": "connected"
      }
    ]
  }
}
```

### **Create Calendar Integration**
```http
POST /api/calendar/integrations
Content-Type: application/json

{
  "provider": "google",
  "access_token": "access-token",
  "refresh_token": "refresh-token",
  "sync_enabled": true
}
```

### **Sync Calendar Events**
```http
POST /api/calendar/integrations/{integration_id}/sync
```

### **List Calendar Events**
```http
GET /api/calendar/events?start_date=2024-01-01&end_date=2024-01-31
```

---

## 👤 **User Management**

### **Get User Profile**
```http
GET /api/users/profile
```

**Response:**
```json
{
  "success": true,
  "data": {
    "user": {
      "id": "user-uuid",
      "email": "user@example.com",
      "username": "johndoe",
      "first_name": "John",
      "last_name": "Doe",
      "theme": "light",
      "timezone": "UTC",
      "language": "en",
      "created_at": "2024-01-01T00:00:00Z"
    }
  }
}
```

### **Update User Profile**
```http
PUT /api/users/profile
Content-Type: application/json

{
  "first_name": "John",
  "last_name": "Doe",
  "theme": "dark",
  "timezone": "America/New_York",
  "language": "en"
}
```

### **Change Password**
```http
POST /api/users/change-password
Content-Type: application/json

{
  "current_password": "oldpassword",
  "new_password": "newpassword123"
}
```

---

## 📦 **Batch Processing**

### **Create Batch Job**
```http
POST /api/batch
Content-Type: application/json

{
  "name": "Q4 Meetings Batch",
  "description": "Process all Q4 meeting recordings",
  "template_id": "template-uuid",
  "files": [
    {
      "filename": "meeting1.mp3",
      "title": "Board Meeting Jan",
      "meeting_date": "2024-01-15T14:00:00Z"
    }
  ]
}
```

### **Upload Batch Files**
```http
POST /api/batch/{batch_id}/upload
Content-Type: multipart/form-data

files: [multiple files]
```

### **Get Batch Status**
```http
GET /api/batch/{batch_id}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "batch_job": {
      "id": "batch-uuid",
      "name": "Q4 Meetings Batch",
      "status": "processing",
      "total_files": 5,
      "processed_files": 3,
      "failed_files": 0,
      "progress_percentage": 60.0,
      "created_at": "2024-01-15T10:00:00Z"
    }
  }
}
```

---

## ❌ **Error Handling**

All API responses follow a consistent error format:

### **Error Response Structure**
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Field 'email' is required",
    "timestamp": "2024-01-15T10:00:00Z",
    "request_id": "req-uuid",
    "field": "email"
  }
}
```

### **HTTP Status Codes**
| Code | Description |
|------|-------------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 409 | Conflict |
| 413 | Payload Too Large |
| 422 | Unprocessable Entity |
| 429 | Too Many Requests |
| 500 | Internal Server Error |

### **Error Codes**
| Code | Description |
|------|-------------|
| `VALIDATION_ERROR` | Input validation failed |
| `AUTH_ERROR` | Authentication failed |
| `AUTHORIZATION_ERROR` | Insufficient permissions |
| `RESOURCE_NOT_FOUND` | Resource doesn't exist |
| `RATE_LIMIT_ERROR` | Rate limit exceeded |
| `FILE_PROCESSING_ERROR` | File processing failed |
| `EXTERNAL_SERVICE_ERROR` | External service error |
| `INTERNAL_ERROR` | Server error |

---

## 🔄 **Rate Limiting**

API requests are rate limited to ensure fair usage:

### **Rate Limits by Endpoint**
| Endpoint | Limit | Window |
|----------|-------|--------|
| Authentication | 5 requests | 5 minutes |
| File Upload | 10 requests | 1 hour |
| Document Comparison | 5 requests | 1 hour |
| General API | 100 requests | 1 hour |

### **Rate Limit Headers**
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1642248000
Retry-After: 3600
```

---

## 🔍 **Interactive API Documentation**

Visit your MinuteMate instance for interactive API documentation:
- **JSON Format:** `/api/docs`
- **HTML Format:** `/api/docs/html`

---

## 📞 **Support**

For API support:
- 📧 Email: api-support@minutemate.com
- 📖 Documentation: [docs.minutemate.com](https://docs.minutemate.com)
- 🐛 Issues: [GitHub Issues](https://github.com/yourusername/minute-mate/issues)
