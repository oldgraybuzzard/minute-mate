#!/usr/bin/env python3
"""
MinuteMate Application Runner
Entry point for running the MinuteMate Flask application.
"""

import os
import sys
from pathlib import Path

# Import the Flask app from current directory
from app import app

if __name__ == "__main__":
    # Set environment variables for development
    os.environ.setdefault('FLASK_ENV', 'development')
    
    print("🧠 Starting MinuteMate API Server...")
    print("=" * 40)
    print(f"Environment: {os.environ.get('FLASK_ENV', 'development')}")
    print(f"Debug mode: {app.config.get('DEBUG', False)}")
    print(f"Upload folder: {app.config.get('UPLOAD_FOLDER')}")
    print(f"Output folder: {app.config.get('OUTPUT_FOLDER')}")
    print("=" * 40)
    print("Server will be available at: http://localhost:5000")
    print("Frontend will be available at: http://localhost:5000/frontend/")
    print("API endpoints:")
    print("  GET  /                    - Health check")
    print("  POST /api/upload          - Upload audio/video file")
    print("  GET  /api/status/<job_id> - Get job status")
    print("  GET  /api/download/<job_id> - Download result")
    print("  GET  /api/jobs            - List all jobs")
    print("  GET  /frontend/           - Web interface")
    print("=" * 40)
    print("Press Ctrl+C to stop the server")
    print()
    
    try:
        # Run the Flask development server
        app.run(
            debug=True,
            host='0.0.0.0',
            port=5000,
            threaded=True
        )
    except KeyboardInterrupt:
        print("\n👋 MinuteMate server stopped.")
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")
        sys.exit(1)
