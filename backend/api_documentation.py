"""
API Documentation generator for MinuteMate
Provides comprehensive API documentation with examples and schemas
"""

import logging
from flask import jsonify, render_template_string
from datetime import datetime

logger = logging.getLogger(__name__)

def get_api_documentation():
    """Get comprehensive API documentation"""
    
    documentation = {
        "info": {
            "title": "MinuteMate API",
            "version": "1.0.0",
            "description": "Comprehensive API for AI-powered meeting minutes generation and management",
            "contact": {
                "name": "MinuteMate Support",
                "email": "support@minutemate.com"
            }
        },
        "servers": [
            {
                "url": "http://localhost:8080",
                "description": "Development server"
            }
        ],
        "paths": {
            "/": {
                "get": {
                    "summary": "Health check",
                    "description": "Basic health check endpoint",
                    "responses": {
                        "200": {
                            "description": "Service is healthy",
                            "example": {
                                "status": "healthy",
                                "service": "MinuteMate API",
                                "version": "1.0.0",
                                "timestamp": "2024-01-01T12:00:00"
                            }
                        }
                    }
                }
            },
            "/api/health": {
                "get": {
                    "summary": "Comprehensive health check",
                    "description": "Detailed health check including database, Redis, filesystem, and AI service status",
                    "responses": {
                        "200": {
                            "description": "Health status with detailed checks",
                            "example": {
                                "status": "healthy",
                                "service": "MinuteMate API",
                                "checks": {
                                    "database": {"status": "healthy"},
                                    "redis": {"status": "healthy"},
                                    "filesystem": {"status": "healthy"},
                                    "ai_service": {"status": "configured"}
                                }
                            }
                        }
                    }
                }
            },
            "/api/auth/register": {
                "post": {
                    "summary": "Register new user",
                    "description": "Create a new user account",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["email", "username", "password", "first_name", "last_name"],
                                    "properties": {
                                        "email": {"type": "string", "format": "email"},
                                        "username": {"type": "string", "minLength": 3, "maxLength": 80},
                                        "password": {"type": "string", "minLength": 8},
                                        "first_name": {"type": "string", "maxLength": 100},
                                        "last_name": {"type": "string", "maxLength": 100}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "201": {"description": "User created successfully"},
                        "400": {"description": "Validation error"},
                        "409": {"description": "User already exists"}
                    }
                }
            },
            "/api/auth/login": {
                "post": {
                    "summary": "User login",
                    "description": "Authenticate user and create session",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["email", "password"],
                                    "properties": {
                                        "email": {"type": "string", "format": "email"},
                                        "password": {"type": "string"}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {"description": "Login successful"},
                        "401": {"description": "Invalid credentials"},
                        "429": {"description": "Rate limit exceeded"}
                    }
                }
            },
            "/api/meetings": {
                "get": {
                    "summary": "List meetings",
                    "description": "Get paginated list of user's meetings",
                    "parameters": [
                        {"name": "page", "in": "query", "schema": {"type": "integer", "default": 1}},
                        {"name": "per_page", "in": "query", "schema": {"type": "integer", "default": 10}},
                        {"name": "status", "in": "query", "schema": {"type": "string", "enum": ["pending", "processing", "completed", "failed"]}},
                        {"name": "search", "in": "query", "schema": {"type": "string"}}
                    ],
                    "responses": {
                        "200": {"description": "List of meetings"},
                        "401": {"description": "Authentication required"}
                    }
                },
                "post": {
                    "summary": "Create meeting",
                    "description": "Upload audio/video file to create new meeting",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "multipart/form-data": {
                                "schema": {
                                    "type": "object",
                                    "required": ["file"],
                                    "properties": {
                                        "file": {"type": "string", "format": "binary"},
                                        "title": {"type": "string"},
                                        "description": {"type": "string"},
                                        "template_id": {"type": "string"}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "201": {"description": "Meeting created and processing started"},
                        "400": {"description": "Invalid file or parameters"},
                        "413": {"description": "File too large"}
                    }
                }
            },
            "/api/meetings/{meeting_id}": {
                "get": {
                    "summary": "Get meeting details",
                    "description": "Get detailed information about a specific meeting",
                    "parameters": [
                        {"name": "meeting_id", "in": "path", "required": True, "schema": {"type": "string"}}
                    ],
                    "responses": {
                        "200": {"description": "Meeting details"},
                        "404": {"description": "Meeting not found"}
                    }
                },
                "delete": {
                    "summary": "Delete meeting",
                    "description": "Delete a meeting and all associated files",
                    "parameters": [
                        {"name": "meeting_id", "in": "path", "required": True, "schema": {"type": "string"}}
                    ],
                    "responses": {
                        "200": {"description": "Meeting deleted successfully"},
                        "404": {"description": "Meeting not found"}
                    }
                }
            },
            "/api/documents/upload-edited/{meeting_id}": {
                "post": {
                    "summary": "Upload edited document",
                    "description": "Upload edited version of meeting minutes to learn user preferences",
                    "parameters": [
                        {"name": "meeting_id", "in": "path", "required": True, "schema": {"type": "string"}}
                    ],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "multipart/form-data": {
                                "schema": {
                                    "type": "object",
                                    "required": ["file"],
                                    "properties": {
                                        "file": {"type": "string", "format": "binary", "description": "DOCX file with user edits"}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {"description": "Document analyzed and preferences learned"},
                        "400": {"description": "Invalid file format"},
                        "404": {"description": "Meeting not found"}
                    }
                }
            },
            "/api/documents/preferences": {
                "get": {
                    "summary": "Get user preferences",
                    "description": "Get all learned user preferences for document formatting",
                    "responses": {
                        "200": {"description": "User preferences organized by category"}
                    }
                }
            },
            "/api/templates": {
                "get": {
                    "summary": "List templates",
                    "description": "Get available meeting templates",
                    "responses": {
                        "200": {"description": "List of templates"}
                    }
                },
                "post": {
                    "summary": "Create template",
                    "description": "Create custom meeting template",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["name", "sections"],
                                    "properties": {
                                        "name": {"type": "string"},
                                        "description": {"type": "string"},
                                        "category": {"type": "string"},
                                        "sections": {"type": "array", "items": {"type": "object"}}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "201": {"description": "Template created successfully"}
                    }
                }
            },
            "/api/calendar/integrations": {
                "get": {
                    "summary": "List calendar integrations",
                    "description": "Get user's calendar integrations",
                    "responses": {
                        "200": {"description": "List of calendar integrations"}
                    }
                },
                "post": {
                    "summary": "Create calendar integration",
                    "description": "Connect to external calendar service",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["provider"],
                                    "properties": {
                                        "provider": {"type": "string", "enum": ["google", "microsoft"]},
                                        "access_token": {"type": "string"},
                                        "refresh_token": {"type": "string"}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "201": {"description": "Integration created successfully"}
                    }
                }
            },
            "/api/batch": {
                "post": {
                    "summary": "Create batch job",
                    "description": "Create batch processing job for multiple files",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["name", "files"],
                                    "properties": {
                                        "name": {"type": "string"},
                                        "description": {"type": "string"},
                                        "template_id": {"type": "string"},
                                        "files": {"type": "array", "items": {"type": "object"}}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "201": {"description": "Batch job created successfully"}
                    }
                }
            }
        },
        "components": {
            "securitySchemes": {
                "sessionAuth": {
                    "type": "apiKey",
                    "in": "cookie",
                    "name": "session"
                }
            },
            "schemas": {
                "Error": {
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean", "example": False},
                        "error": {
                            "type": "object",
                            "properties": {
                                "code": {"type": "string"},
                                "message": {"type": "string"},
                                "timestamp": {"type": "string", "format": "date-time"},
                                "request_id": {"type": "string"}
                            }
                        }
                    }
                },
                "Success": {
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean", "example": True},
                        "message": {"type": "string"},
                        "data": {"type": "object"}
                    }
                }
            }
        },
        "security": [
            {"sessionAuth": []}
        ]
    }
    
    return documentation

def add_documentation_endpoints(app):
    """Add API documentation endpoints"""
    
    @app.route('/api/docs')
    def api_documentation():
        """Get API documentation in JSON format"""
        return jsonify(get_api_documentation())
    
    @app.route('/api/docs/html')
    def api_documentation_html():
        """Get API documentation as HTML page"""
        docs = get_api_documentation()
        
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>{{ docs.info.title }} - API Documentation</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
                .header { border-bottom: 2px solid #333; padding-bottom: 20px; margin-bottom: 30px; }
                .endpoint { margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }
                .method { display: inline-block; padding: 4px 8px; border-radius: 3px; color: white; font-weight: bold; }
                .get { background-color: #61affe; }
                .post { background-color: #49cc90; }
                .put { background-color: #fca130; }
                .delete { background-color: #f93e3e; }
                .path { font-family: monospace; font-size: 1.1em; margin: 10px 0; }
                .description { color: #666; margin: 10px 0; }
                .schema { background-color: #f8f8f8; padding: 10px; border-radius: 3px; font-family: monospace; }
                .example { background-color: #f0f8ff; padding: 10px; border-radius: 3px; font-family: monospace; }
                pre { white-space: pre-wrap; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>{{ docs.info.title }}</h1>
                <p>{{ docs.info.description }}</p>
                <p><strong>Version:</strong> {{ docs.info.version }}</p>
                <p><strong>Generated:</strong> {{ timestamp }}</p>
            </div>
            
            <h2>Endpoints</h2>
            {% for path, methods in docs.paths.items() %}
                {% for method, details in methods.items() %}
                <div class="endpoint">
                    <div>
                        <span class="method {{ method }}">{{ method.upper() }}</span>
                        <span class="path">{{ path }}</span>
                    </div>
                    <h3>{{ details.summary }}</h3>
                    <div class="description">{{ details.description }}</div>
                    
                    {% if details.parameters %}
                    <h4>Parameters</h4>
                    <ul>
                        {% for param in details.parameters %}
                        <li><strong>{{ param.name }}</strong> ({{ param.in }}) - {{ param.schema.type }}
                            {% if param.required %}<em>required</em>{% endif %}
                        </li>
                        {% endfor %}
                    </ul>
                    {% endif %}
                    
                    {% if details.requestBody %}
                    <h4>Request Body</h4>
                    <div class="schema">{{ details.requestBody | tojson }}</div>
                    {% endif %}
                    
                    <h4>Responses</h4>
                    <ul>
                        {% for code, response in details.responses.items() %}
                        <li><strong>{{ code }}</strong> - {{ response.description }}
                            {% if response.example %}
                            <div class="example">
                                <strong>Example:</strong>
                                <pre>{{ response.example | tojson(indent=2) }}</pre>
                            </div>
                            {% endif %}
                        </li>
                        {% endfor %}
                    </ul>
                </div>
                {% endfor %}
            {% endfor %}
            
            <h2>Rate Limiting</h2>
            <p>API requests are rate limited to prevent abuse:</p>
            <ul>
                <li>Authentication endpoints: 5 requests per 5 minutes</li>
                <li>File upload endpoints: 10 requests per hour</li>
                <li>General API endpoints: 100 requests per hour</li>
            </ul>
            
            <h2>Error Handling</h2>
            <p>All API responses follow a consistent format. Errors include detailed information:</p>
            <div class="example">
                <pre>{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Field 'email' is required",
    "timestamp": "2024-01-01T12:00:00Z",
    "request_id": "uuid-here"
  }
}</pre>
            </div>
        </body>
        </html>
        """
        
        from jinja2 import Template
        template = Template(html_template)
        
        return template.render(
            docs=docs,
            timestamp=datetime.now().isoformat()
        )
    
    logger.info("API documentation endpoints added")
