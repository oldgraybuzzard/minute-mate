#!/usr/bin/env python3
"""
MinuteMate Flask Application Test Script
Simple test script to verify the Flask application is working correctly.
"""

import requests
import json
import os
import tempfile
from pathlib import Path

# Configuration
BASE_URL = "http://localhost:5000"
TEST_AUDIO_FILE = "test_audio.wav"

def create_test_audio_file():
    """Create a simple test audio file for testing"""
    try:
        # Create a minimal WAV file (just headers, no actual audio data)
        # This is just for testing the upload functionality
        wav_header = b'RIFF\x24\x08\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x44\xac\x00\x00\x88X\x01\x00\x02\x00\x10\x00data\x00\x08\x00\x00'
        
        with open(TEST_AUDIO_FILE, 'wb') as f:
            f.write(wav_header)
            # Add some dummy audio data
            f.write(b'\x00' * 2048)
        
        print(f"✓ Created test audio file: {TEST_AUDIO_FILE}")
        return True
    except Exception as e:
        print(f"✗ Failed to create test audio file: {e}")
        return False

def test_health_endpoint():
    """Test the health check endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/")
        if response.status_code == 200:
            data = response.json()
            print("✓ Health check passed")
            print(f"  API Version: {data.get('version')}")
            print(f"  Status: {data.get('status')}")
            return True
        else:
            print(f"✗ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Health check error: {e}")
        return False

def test_file_upload():
    """Test file upload functionality"""
    if not os.path.exists(TEST_AUDIO_FILE):
        if not create_test_audio_file():
            return False
    
    try:
        with open(TEST_AUDIO_FILE, 'rb') as f:
            files = {'file': (TEST_AUDIO_FILE, f, 'audio/wav')}
            response = requests.post(f"{BASE_URL}/api/upload", files=files)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                job_id = data['data']['job_id']
                print("✓ File upload successful")
                print(f"  Job ID: {job_id}")
                print(f"  Filename: {data['data']['filename']}")
                print(f"  File Size: {data['data']['file_size']}")
                return job_id
            else:
                print(f"✗ Upload failed: {data.get('message')}")
                return None
        else:
            print(f"✗ Upload failed: {response.status_code}")
            print(f"  Response: {response.text}")
            return None
    except Exception as e:
        print(f"✗ Upload error: {e}")
        return None

def test_job_status(job_id):
    """Test job status endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/api/status/{job_id}")
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                job_info = data['data']
                print("✓ Job status retrieved")
                print(f"  Status: {job_info['status']}")
                print(f"  Stage: {job_info['stage']}")
                print(f"  Progress: {job_info['progress']}%")
                print(f"  Message: {job_info['message']}")
                return True
            else:
                print(f"✗ Status check failed: {data.get('message')}")
                return False
        else:
            print(f"✗ Status check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Status check error: {e}")
        return False

def test_jobs_list():
    """Test jobs list endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/api/jobs")
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                jobs = data['data']['jobs']
                print(f"✓ Jobs list retrieved ({len(jobs)} jobs)")
                for job_id, job_info in jobs.items():
                    print(f"  {job_id}: {job_info['status']} - {job_info['filename']}")
                return True
            else:
                print(f"✗ Jobs list failed: {data.get('message')}")
                return False
        else:
            print(f"✗ Jobs list failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Jobs list error: {e}")
        return False

def cleanup():
    """Clean up test files"""
    try:
        if os.path.exists(TEST_AUDIO_FILE):
            os.remove(TEST_AUDIO_FILE)
            print(f"✓ Cleaned up test file: {TEST_AUDIO_FILE}")
    except Exception as e:
        print(f"✗ Cleanup error: {e}")

def main():
    """Run all tests"""
    print("🧠 MinuteMate API Test Suite")
    print("=" * 40)
    
    # Test health endpoint
    print("\n1. Testing health endpoint...")
    if not test_health_endpoint():
        print("❌ Health check failed. Is the server running?")
        return
    
    # Test file upload
    print("\n2. Testing file upload...")
    job_id = test_file_upload()
    if not job_id:
        print("❌ File upload failed")
        cleanup()
        return
    
    # Test job status
    print("\n3. Testing job status...")
    if not test_job_status(job_id):
        print("❌ Job status check failed")
        cleanup()
        return
    
    # Test jobs list
    print("\n4. Testing jobs list...")
    if not test_jobs_list():
        print("❌ Jobs list failed")
        cleanup()
        return
    
    print("\n✅ All tests passed!")
    print("\n🎉 MinuteMate Flask application is working correctly!")
    
    # Cleanup
    cleanup()

if __name__ == "__main__":
    main()
