# 🔗 MinuteMate Integrations Guide

Complete guide to integrating MinuteMate with your existing tools and workflows.

## 📋 **Table of Contents**
- [Calendar Integrations](#calendar-integrations)
- [Video Conferencing](#video-conferencing)
- [Cloud Storage](#cloud-storage)
- [Project Management](#project-management)
- [Communication Tools](#communication-tools)
- [API Integrations](#api-integrations)
- [Webhooks](#webhooks)

---

## 📅 **Calendar Integrations**

### **Google Calendar**

#### **Setup Process**
1. **Enable Google Calendar API** in Google Cloud Console
2. **Create OAuth 2.0 credentials**
3. **Configure redirect URI**: `https://your-app.railway.app/auth/google/callback`
4. **Add credentials to MinuteMate**

#### **Configuration**
```bash
# Environment variables
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_REDIRECT_URI=https://your-app.railway.app/auth/google/callback
```

#### **Features**
- ✅ **Automatic Meeting Detection** - Sync calendar events
- ✅ **Meeting Metadata** - Import attendees, agenda, location
- ✅ **Bi-directional Sync** - Update calendar with meeting results
- ✅ **Recurring Meetings** - Handle series and exceptions
- ✅ **Time Zone Support** - Respect user time zones

#### **API Usage**
```python
# Connect Google Calendar
POST /api/calendar/integrations
{
  "provider": "google",
  "access_token": "google-access-token",
  "refresh_token": "google-refresh-token"
}

# Sync calendar events
POST /api/calendar/integrations/{integration_id}/sync
{
  "start_date": "2024-01-01",
  "end_date": "2024-01-31"
}

# Get calendar events
GET /api/calendar/events?provider=google&start_date=2024-01-01
```

### **Microsoft Outlook**

#### **Setup Process**
1. **Register app** in Azure Active Directory
2. **Configure API permissions** for Calendar.ReadWrite
3. **Set redirect URI**: `https://your-app.railway.app/auth/microsoft/callback`
4. **Add credentials to MinuteMate**

#### **Configuration**
```bash
# Environment variables
MICROSOFT_CLIENT_ID=your-microsoft-client-id
MICROSOFT_CLIENT_SECRET=your-microsoft-client-secret
MICROSOFT_REDIRECT_URI=https://your-app.railway.app/auth/microsoft/callback
```

#### **Features**
- ✅ **Exchange Integration** - Works with Exchange Server
- ✅ **Office 365 Support** - Full O365 compatibility
- ✅ **Teams Meeting Detection** - Identify Teams meetings
- ✅ **Shared Calendars** - Access team calendars
- ✅ **Meeting Rooms** - Resource booking integration

### **Apple Calendar (CalDAV)**

#### **Setup Process**
1. **Enable CalDAV** in MinuteMate settings
2. **Configure iCloud credentials** or CalDAV server
3. **Set up calendar sync** preferences

#### **Configuration**
```bash
# CalDAV settings
CALDAV_SERVER=https://caldav.icloud.com
CALDAV_USERNAME=your-apple-id
CALDAV_PASSWORD=app-specific-password
```

---

## 🎥 **Video Conferencing**

### **Zoom Integration**

#### **Recording Access**
```python
# Process Zoom recording from URL
POST /api/upload-url
{
  "url": "https://zoom.us/rec/share/recording-url",
  "title": "Board Meeting Q4",
  "meeting_date": "2024-01-15T14:00:00Z"
}

# Automatic Zoom webhook processing
POST /api/webhooks/zoom
{
  "event": "recording.completed",
  "payload": {
    "recording_files": [
      {
        "download_url": "https://zoom.us/rec/download/...",
        "file_type": "MP4"
      }
    ]
  }
}
```

#### **Features**
- ✅ **Automatic Processing** - Process recordings when available
- ✅ **Multiple Formats** - Audio and video support
- ✅ **Participant Data** - Import attendee information
- ✅ **Chat Integration** - Include chat messages in minutes
- ✅ **Breakout Rooms** - Handle separate room recordings

### **Microsoft Teams**

#### **Setup Process**
1. **Register app** in Azure AD
2. **Configure Graph API permissions**
3. **Set up webhook endpoints**
4. **Enable recording access**

#### **Features**
- ✅ **Teams Recording Access** - Download meeting recordings
- ✅ **Chat Integration** - Include Teams chat in minutes
- ✅ **Participant Tracking** - Attendance and participation data
- ✅ **Channel Meetings** - Support for channel-based meetings

### **Google Meet**

#### **Recording Processing**
```python
# Process Google Meet recording
POST /api/upload-url
{
  "url": "https://drive.google.com/file/d/recording-id/view",
  "title": "Team Standup",
  "template_id": "standup-template"
}
```

#### **Features**
- ✅ **Drive Integration** - Access recordings from Google Drive
- ✅ **Automatic Detection** - Identify Meet recordings
- ✅ **Participant Data** - Import attendee information
- ✅ **Calendar Sync** - Link with Google Calendar events

---

## ☁️ **Cloud Storage**

### **Google Drive**

#### **Setup**
```bash
# Google Drive API credentials
GOOGLE_DRIVE_CLIENT_ID=your-client-id
GOOGLE_DRIVE_CLIENT_SECRET=your-client-secret
```

#### **Features**
- ✅ **Automatic Upload** - Save minutes to Drive
- ✅ **Folder Organization** - Organize by date/project
- ✅ **Sharing Controls** - Respect Drive permissions
- ✅ **Version History** - Track document changes

### **Dropbox**

#### **Configuration**
```bash
# Dropbox API settings
DROPBOX_APP_KEY=your-app-key
DROPBOX_APP_SECRET=your-app-secret
```

#### **Features**
- ✅ **File Sync** - Sync minutes to Dropbox
- ✅ **Team Folders** - Organize by team/project
- ✅ **Link Sharing** - Generate shareable links
- ✅ **Backup Storage** - Automatic backup of recordings

### **OneDrive**

#### **Integration**
```python
# OneDrive file upload
POST /api/integrations/onedrive/upload
{
  "meeting_id": "meeting-uuid",
  "folder_path": "/Meetings/2024/Q1",
  "format": "docx"
}
```

---

## 📊 **Project Management**

### **Asana Integration**

#### **Task Creation**
```python
# Create Asana tasks from action items
POST /api/integrations/asana/create-tasks
{
  "meeting_id": "meeting-uuid",
  "project_id": "asana-project-id",
  "assignee_mapping": {
    "John Doe": "john.doe@company.com",
    "Jane Smith": "jane.smith@company.com"
  }
}
```

#### **Features**
- ✅ **Action Item Sync** - Convert to Asana tasks
- ✅ **Project Mapping** - Link to specific projects
- ✅ **Due Date Sync** - Set task deadlines
- ✅ **Progress Tracking** - Monitor task completion

### **Trello Integration**

#### **Card Creation**
```python
# Create Trello cards from meeting outcomes
POST /api/integrations/trello/create-cards
{
  "meeting_id": "meeting-uuid",
  "board_id": "trello-board-id",
  "list_mapping": {
    "action_items": "To Do",
    "decisions": "Decided",
    "follow_ups": "Follow Up"
  }
}
```

### **Jira Integration**

#### **Issue Creation**
```python
# Create Jira issues from action items
POST /api/integrations/jira/create-issues
{
  "meeting_id": "meeting-uuid",
  "project_key": "PROJ",
  "issue_type": "Task",
  "assignee_mapping": {
    "John Doe": "jdoe",
    "Jane Smith": "jsmith"
  }
}
```

---

## 💬 **Communication Tools**

### **Slack Integration**

#### **Setup**
1. **Create Slack app** in your workspace
2. **Configure OAuth scopes**: `chat:write`, `files:write`
3. **Set up webhook URL**: `https://your-app.railway.app/webhooks/slack`
4. **Install app** to workspace

#### **Features**
```python
# Send meeting summary to Slack
POST /api/integrations/slack/send-summary
{
  "meeting_id": "meeting-uuid",
  "channel": "#general",
  "include_action_items": true,
  "mention_assignees": true
}

# Slack webhook for meeting notifications
POST /webhooks/slack
{
  "event": {
    "type": "message",
    "text": "Process meeting recording",
    "files": [
      {
        "url_private": "https://files.slack.com/...",
        "mimetype": "audio/mp3"
      }
    ]
  }
}
```

#### **Capabilities**
- ✅ **Meeting Summaries** - Post to channels
- ✅ **Action Item Notifications** - Mention assignees
- ✅ **File Processing** - Process recordings from Slack
- ✅ **Bot Commands** - Slash commands for quick actions

### **Microsoft Teams**

#### **Bot Integration**
```python
# Teams bot for meeting management
POST /api/integrations/teams/send-message
{
  "meeting_id": "meeting-uuid",
  "team_id": "teams-team-id",
  "channel_id": "teams-channel-id",
  "message_type": "summary"
}
```

#### **Features**
- ✅ **Adaptive Cards** - Rich meeting summaries
- ✅ **Action Item Cards** - Interactive task management
- ✅ **File Sharing** - Share minutes in Teams
- ✅ **Meeting Integration** - Link with Teams meetings

### **Discord Integration**

#### **Webhook Setup**
```python
# Discord webhook for meeting notifications
POST /api/integrations/discord/webhook
{
  "webhook_url": "https://discord.com/api/webhooks/...",
  "meeting_id": "meeting-uuid",
  "embed_type": "summary"
}
```

---

## 🔌 **API Integrations**

### **REST API**

#### **Authentication**
```bash
# Session-based authentication
curl -X POST https://your-app.railway.app/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password"}'

# Use session cookie for subsequent requests
curl -X GET https://your-app.railway.app/api/meetings \
  -H "Cookie: session=session-cookie-value"
```

#### **Common Endpoints**
```bash
# Upload meeting recording
curl -X POST https://your-app.railway.app/api/meetings \
  -F "file=@meeting.mp3" \
  -F "title=Board Meeting" \
  -F "template_id=board-template"

# Get meeting status
curl -X GET https://your-app.railway.app/api/meetings/{meeting_id}

# Download meeting minutes
curl -X GET https://your-app.railway.app/api/meetings/{meeting_id}/download?format=docx \
  -o meeting_minutes.docx
```

### **GraphQL API (Coming Soon)**

#### **Schema Example**
```graphql
type Meeting {
  id: ID!
  title: String!
  description: String
  status: MeetingStatus!
  createdAt: DateTime!
  participants: [String!]!
  actionItems: [ActionItem!]!
  documents: [Document!]!
}

type Query {
  meetings(first: Int, after: String): MeetingConnection!
  meeting(id: ID!): Meeting
}

type Mutation {
  createMeeting(input: CreateMeetingInput!): Meeting!
  updateMeeting(id: ID!, input: UpdateMeetingInput!): Meeting!
}
```

---

## 🪝 **Webhooks**

### **Webhook Configuration**

#### **Setup**
```python
# Configure webhook endpoints
POST /api/webhooks
{
  "url": "https://your-app.com/minutemate-webhook",
  "events": [
    "meeting.created",
    "meeting.completed",
    "meeting.failed"
  ],
  "secret": "webhook-secret-key"
}
```

#### **Event Types**
| Event | Description |
|-------|-------------|
| `meeting.created` | New meeting uploaded |
| `meeting.processing` | Processing started |
| `meeting.completed` | Processing finished successfully |
| `meeting.failed` | Processing failed |
| `document.generated` | Minutes document created |
| `preferences.updated` | User preferences learned |

### **Webhook Payload**

#### **Meeting Completed Event**
```json
{
  "event": "meeting.completed",
  "timestamp": "2024-01-15T10:30:00Z",
  "data": {
    "meeting": {
      "id": "meeting-uuid",
      "title": "Board Meeting Q4",
      "status": "completed",
      "duration_minutes": 90,
      "participant_count": 8,
      "action_items_count": 5,
      "download_urls": {
        "docx": "https://your-app.railway.app/api/meetings/meeting-uuid/download?format=docx",
        "html": "https://your-app.railway.app/api/meetings/meeting-uuid/download?format=html",
        "json": "https://your-app.railway.app/api/meetings/meeting-uuid/download?format=json"
      }
    }
  },
  "signature": "sha256=webhook-signature"
}
```

### **Webhook Security**

#### **Signature Verification**
```python
import hmac
import hashlib

def verify_webhook_signature(payload, signature, secret):
    """Verify webhook signature for security."""
    expected_signature = hmac.new(
        secret.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(
        f"sha256={expected_signature}",
        signature
    )
```

---

## 🔧 **Custom Integrations**

### **SDK Development**

#### **Python SDK Example**
```python
from minutemate import MinuteMateClient

# Initialize client
client = MinuteMateClient(
    base_url="https://your-app.railway.app",
    api_key="your-api-key"
)

# Upload meeting
meeting = client.meetings.create(
    file_path="meeting.mp3",
    title="Team Standup",
    template_id="standup-template"
)

# Wait for processing
meeting.wait_for_completion(timeout=300)

# Download results
meeting.download("docx", "meeting_minutes.docx")
```

#### **JavaScript SDK Example**
```javascript
import { MinuteMateClient } from '@minutemate/sdk';

const client = new MinuteMateClient({
  baseUrl: 'https://your-app.railway.app',
  apiKey: 'your-api-key'
});

// Upload and process meeting
const meeting = await client.meetings.create({
  file: audioFile,
  title: 'Team Standup',
  templateId: 'standup-template'
});

// Monitor progress
await meeting.waitForCompletion();

// Download results
const docxBlob = await meeting.download('docx');
```

---

## 📞 **Integration Support**

For integration help:
- 📧 **Email:** integrations@minutemate.com
- 📖 **Documentation:** [docs.minutemate.com/integrations](https://docs.minutemate.com/integrations)
- 💬 **Discord:** [Join our community](https://discord.gg/minutemate)
- 🛠️ **SDK Repository:** [github.com/minutemate/sdks](https://github.com/minutemate/sdks)
