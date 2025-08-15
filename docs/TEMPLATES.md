# 🎨 MinuteMate Templates Guide

Complete guide to creating, customizing, and using meeting templates in MinuteMate.

## 📋 **Table of Contents**
- [Template Overview](#template-overview)
- [Pre-built Templates](#pre-built-templates)
- [Creating Custom Templates](#creating-custom-templates)
- [Template Sections](#template-sections)
- [Robert's Rules Templates](#roberts-rules-templates)
- [Industry-Specific Templates](#industry-specific-templates)
- [Template Management](#template-management)

---

## 📖 **Template Overview**

Templates in MinuteMate define the structure and formatting of your meeting minutes. They ensure consistency across meetings and can be customized to match your organization's specific needs.

### **Template Components**
- **Sections:** Structured parts of the meeting (e.g., Call to Order, Discussion)
- **Formatting:** Font, size, spacing, and style preferences
- **Prompts:** AI guidance for generating specific content
- **Rules:** Validation and requirements for each section

---

## 📚 **Pre-built Templates**

MinuteMate includes 50+ professionally designed templates for various meeting types.

### **General Business Templates**

#### **Standard Meeting Template**
```json
{
  "name": "Standard Meeting",
  "category": "general",
  "sections": [
    {
      "name": "Meeting Information",
      "type": "header",
      "required": true,
      "fields": ["date", "time", "location", "attendees"]
    },
    {
      "name": "Agenda Review",
      "type": "list",
      "required": true,
      "prompt": "List agenda items discussed"
    },
    {
      "name": "Discussion Points",
      "type": "text",
      "required": true,
      "prompt": "Summarize key discussion points"
    },
    {
      "name": "Action Items",
      "type": "action_items",
      "required": true,
      "fields": ["task", "assignee", "due_date"]
    },
    {
      "name": "Next Meeting",
      "type": "text",
      "required": false,
      "prompt": "Date and agenda for next meeting"
    }
  ]
}
```

#### **Team Standup Template**
```json
{
  "name": "Daily Standup",
  "category": "agile",
  "sections": [
    {
      "name": "Meeting Details",
      "type": "header",
      "required": true
    },
    {
      "name": "Yesterday's Accomplishments",
      "type": "list",
      "required": true,
      "prompt": "What was completed yesterday"
    },
    {
      "name": "Today's Goals",
      "type": "list",
      "required": true,
      "prompt": "What will be worked on today"
    },
    {
      "name": "Blockers",
      "type": "list",
      "required": false,
      "prompt": "Any impediments or blockers"
    },
    {
      "name": "Action Items",
      "type": "action_items",
      "required": false
    }
  ]
}
```

### **Executive Templates**

#### **Board Meeting Template**
```json
{
  "name": "Board Meeting",
  "category": "executive",
  "roberts_rules": true,
  "sections": [
    {
      "name": "Call to Order",
      "type": "text",
      "required": true,
      "prompt": "Meeting called to order by [Chair] at [time]"
    },
    {
      "name": "Roll Call",
      "type": "attendees",
      "required": true,
      "fields": ["present", "absent", "guests"]
    },
    {
      "name": "Approval of Previous Minutes",
      "type": "motion",
      "required": true,
      "fields": ["motion", "seconded_by", "vote_result"]
    },
    {
      "name": "Financial Report",
      "type": "text",
      "required": true,
      "prompt": "Financial status and key metrics"
    },
    {
      "name": "Committee Reports",
      "type": "sections",
      "required": false,
      "subsections": ["audit", "governance", "compensation"]
    },
    {
      "name": "New Business",
      "type": "text",
      "required": false
    },
    {
      "name": "Motions and Resolutions",
      "type": "motions",
      "required": false,
      "fields": ["motion", "moved_by", "seconded_by", "discussion", "vote"]
    },
    {
      "name": "Adjournment",
      "type": "text",
      "required": true,
      "prompt": "Meeting adjourned at [time]"
    }
  ]
}
```

---

## 🛠️ **Creating Custom Templates**

### **Template Builder Interface**

1. **Navigate to Templates** in the dashboard
2. **Click "Create Template"**
3. **Choose template type:**
   - Start from scratch
   - Copy existing template
   - Import from file

### **Template Configuration**

#### **Basic Information**
```json
{
  "name": "My Custom Template",
  "description": "Template for weekly team meetings",
  "category": "team",
  "is_public": false,
  "tags": ["weekly", "team", "status"]
}
```

#### **Formatting Options**
```json
{
  "formatting": {
    "font_family": "Arial",
    "font_size": 12,
    "line_spacing": 1.5,
    "margin_top": 1.0,
    "margin_bottom": 1.0,
    "margin_left": 1.0,
    "margin_right": 1.0,
    "header_style": {
      "font_size": 16,
      "bold": true,
      "color": "#000000"
    },
    "subheader_style": {
      "font_size": 14,
      "bold": true,
      "color": "#333333"
    }
  }
}
```

---

## 📝 **Template Sections**

### **Section Types**

#### **Header Section**
```json
{
  "name": "Meeting Information",
  "type": "header",
  "required": true,
  "fields": [
    {
      "name": "meeting_title",
      "label": "Meeting Title",
      "type": "text",
      "required": true
    },
    {
      "name": "date",
      "label": "Date",
      "type": "date",
      "required": true
    },
    {
      "name": "time",
      "label": "Time",
      "type": "time",
      "required": true
    },
    {
      "name": "location",
      "label": "Location",
      "type": "text",
      "required": false
    }
  ]
}
```

#### **Text Section**
```json
{
  "name": "Executive Summary",
  "type": "text",
  "required": true,
  "prompt": "Provide a brief summary of the meeting's key outcomes",
  "min_length": 50,
  "max_length": 500,
  "formatting": {
    "style": "paragraph",
    "indent": false
  }
}
```

#### **List Section**
```json
{
  "name": "Agenda Items",
  "type": "list",
  "required": true,
  "prompt": "List all agenda items discussed",
  "list_style": "numbered",
  "allow_nested": true,
  "max_items": 20
}
```

#### **Action Items Section**
```json
{
  "name": "Action Items",
  "type": "action_items",
  "required": true,
  "fields": [
    {
      "name": "task",
      "label": "Task Description",
      "type": "text",
      "required": true
    },
    {
      "name": "assignee",
      "label": "Assigned To",
      "type": "text",
      "required": true
    },
    {
      "name": "due_date",
      "label": "Due Date",
      "type": "date",
      "required": false
    },
    {
      "name": "priority",
      "label": "Priority",
      "type": "select",
      "options": ["High", "Medium", "Low"],
      "required": false
    }
  ]
}
```

#### **Attendees Section**
```json
{
  "name": "Attendees",
  "type": "attendees",
  "required": true,
  "fields": [
    {
      "name": "present",
      "label": "Present",
      "type": "list",
      "required": true
    },
    {
      "name": "absent",
      "label": "Absent",
      "type": "list",
      "required": false
    },
    {
      "name": "guests",
      "label": "Guests",
      "type": "list",
      "required": false
    }
  ]
}
```

#### **Motion Section (Robert's Rules)**
```json
{
  "name": "Motion",
  "type": "motion",
  "required": false,
  "fields": [
    {
      "name": "motion_text",
      "label": "Motion",
      "type": "text",
      "required": true
    },
    {
      "name": "moved_by",
      "label": "Moved By",
      "type": "text",
      "required": true
    },
    {
      "name": "seconded_by",
      "label": "Seconded By",
      "type": "text",
      "required": true
    },
    {
      "name": "discussion",
      "label": "Discussion",
      "type": "text",
      "required": false
    },
    {
      "name": "vote_result",
      "label": "Vote Result",
      "type": "select",
      "options": ["Passed", "Failed", "Tabled"],
      "required": true
    },
    {
      "name": "vote_count",
      "label": "Vote Count",
      "type": "object",
      "fields": [
        {"name": "for", "type": "number"},
        {"name": "against", "type": "number"},
        {"name": "abstain", "type": "number"}
      ]
    }
  ]
}
```

---

## ⚖️ **Robert's Rules Templates**

MinuteMate includes specialized templates for formal meetings following Robert's Rules of Order.

### **Formal Board Meeting Template**
```json
{
  "name": "Formal Board Meeting (Robert's Rules)",
  "category": "roberts_rules",
  "roberts_rules_compliance": true,
  "sections": [
    {
      "name": "Call to Order",
      "type": "text",
      "required": true,
      "roberts_rules": {
        "order": 1,
        "description": "Meeting officially begins"
      }
    },
    {
      "name": "Roll Call and Establishment of Quorum",
      "type": "attendees",
      "required": true,
      "roberts_rules": {
        "order": 2,
        "quorum_required": true
      }
    },
    {
      "name": "Approval of Agenda",
      "type": "motion",
      "required": true,
      "roberts_rules": {
        "order": 3,
        "motion_type": "procedural"
      }
    },
    {
      "name": "Approval of Previous Minutes",
      "type": "motion",
      "required": true,
      "roberts_rules": {
        "order": 4,
        "motion_type": "procedural"
      }
    },
    {
      "name": "Reports",
      "type": "sections",
      "required": false,
      "roberts_rules": {
        "order": 5
      },
      "subsections": [
        "Officers' Reports",
        "Committee Reports",
        "Special Reports"
      ]
    },
    {
      "name": "Unfinished Business",
      "type": "text",
      "required": false,
      "roberts_rules": {
        "order": 6
      }
    },
    {
      "name": "New Business",
      "type": "motions",
      "required": false,
      "roberts_rules": {
        "order": 7
      }
    },
    {
      "name": "Announcements",
      "type": "list",
      "required": false,
      "roberts_rules": {
        "order": 8
      }
    },
    {
      "name": "Adjournment",
      "type": "motion",
      "required": true,
      "roberts_rules": {
        "order": 9,
        "motion_type": "procedural"
      }
    }
  ]
}
```

### **Robert's Rules Features**
- **Automatic motion formatting**
- **Vote tracking and validation**
- **Quorum verification**
- **Parliamentary procedure compliance**
- **Proper motion language**

---

## 🏢 **Industry-Specific Templates**

### **Healthcare Templates**

#### **Medical Staff Meeting**
```json
{
  "name": "Medical Staff Meeting",
  "category": "healthcare",
  "compliance": ["HIPAA"],
  "sections": [
    {
      "name": "Credentialing Committee Report",
      "type": "text",
      "required": true,
      "confidential": true
    },
    {
      "name": "Quality Assurance Review",
      "type": "text",
      "required": true,
      "confidential": true
    },
    {
      "name": "Patient Safety Initiatives",
      "type": "list",
      "required": true
    }
  ]
}
```

### **Legal Templates**

#### **Legal Team Meeting**
```json
{
  "name": "Legal Team Meeting",
  "category": "legal",
  "sections": [
    {
      "name": "Case Status Updates",
      "type": "sections",
      "required": true,
      "confidential": true
    },
    {
      "name": "Regulatory Updates",
      "type": "text",
      "required": true
    },
    {
      "name": "Risk Assessment",
      "type": "text",
      "required": true,
      "confidential": true
    }
  ]
}
```

### **Educational Templates**

#### **Faculty Meeting**
```json
{
  "name": "Faculty Meeting",
  "category": "education",
  "sections": [
    {
      "name": "Academic Affairs",
      "type": "text",
      "required": true
    },
    {
      "name": "Student Performance Review",
      "type": "text",
      "required": true,
      "confidential": true
    },
    {
      "name": "Curriculum Updates",
      "type": "list",
      "required": true
    }
  ]
}
```

---

## 🔧 **Template Management**

### **Template Operations**

#### **Import Template**
```bash
# Upload template file (JSON format)
POST /api/templates/import
Content-Type: multipart/form-data

file: template.json
```

#### **Export Template**
```bash
# Download template as JSON
GET /api/templates/{template_id}/export
```

#### **Share Template**
```bash
# Make template public
PUT /api/templates/{template_id}
{
  "is_public": true
}
```

### **Template Validation**

MinuteMate automatically validates templates:
- ✅ Required sections are present
- ✅ Field types are valid
- ✅ Robert's Rules compliance (if enabled)
- ✅ Formatting options are supported
- ✅ Section dependencies are met

### **Template Versioning**

Templates support versioning for change tracking:
```json
{
  "version": "1.2.0",
  "changelog": [
    {
      "version": "1.2.0",
      "date": "2024-01-15",
      "changes": ["Added action items section", "Updated formatting"]
    }
  ]
}
```

---

## 🎯 **Best Practices**

### **Template Design**
1. **Keep it simple** - Start with essential sections
2. **Use clear names** - Section names should be self-explanatory
3. **Provide good prompts** - Help AI generate better content
4. **Test thoroughly** - Validate with sample meetings
5. **Iterate based on feedback** - Improve based on usage

### **Section Organization**
1. **Logical flow** - Order sections chronologically
2. **Group related content** - Keep similar items together
3. **Use subsections** - Break down complex topics
4. **Mark required fields** - Ensure critical information is captured

### **Formatting Guidelines**
1. **Consistent styling** - Use uniform fonts and spacing
2. **Professional appearance** - Choose readable fonts and sizes
3. **Brand compliance** - Match organizational standards
4. **Accessibility** - Ensure good contrast and readability

---

## 📞 **Support**

For template help:
- 📧 Email: templates@minutemate.com
- 📖 Documentation: [docs.minutemate.com](https://docs.minutemate.com)
- 🎨 Template Gallery: [templates.minutemate.com](https://templates.minutemate.com)
