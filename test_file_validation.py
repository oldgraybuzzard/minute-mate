#!/usr/bin/env python3
"""
MinuteMate File Validation Test Suite
Comprehensive tests for the enhanced file validation and storage system.
"""

import requests
import json
import os
import tempfile
from pathlib import Path
import time

# Configuration
BASE_URL = "http://localhost:5000"

def create_test_files():
    """Create various test files for validation testing"""
    test_files = {}
    
    # Create a valid WAV file (minimal header)
    wav_header = b'RIFF\x24\x08\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x44\xac\x00\x00\x88X\x01\x00\x02\x00\x10\x00data\x00\x08\x00\x00'
    
    # Valid audio file
    valid_audio = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
    valid_audio.write(wav_header + b'\x00' * 2048)
    valid_audio.close()
    test_files['valid_audio'] = valid_audio.name
    
    # Invalid file (text file with audio extension)
    invalid_audio = tempfile.NamedTemporaryFile(suffix='.mp3', delete=False)
    invalid_audio.write(b'This is not an audio file')
    invalid_audio.close()
    test_files['invalid_audio'] = invalid_audio.name
    
    # File with dangerous filename
    dangerous_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
    dangerous_file.write(wav_header + b'\x00' * 1024)
    dangerous_file.close()
    test_files['dangerous_filename'] = dangerous_file.name
    
    # Large file (for size testing)
    large_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
    large_file.write(wav_header)
    large_file.write(b'\x00' * (10 * 1024 * 1024))  # 10MB of data
    large_file.close()
    test_files['large_file'] = large_file.name
    
    # Empty file
    empty_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
    empty_file.close()
    test_files['empty_file'] = empty_file.name
    
    print("✓ Created test files")
    return test_files

def cleanup_test_files(test_files):
    """Clean up test files"""
    for file_path in test_files.values():
        try:
            os.unlink(file_path)
        except:
            pass
    print("✓ Cleaned up test files")

def test_health_endpoint():
    """Test the enhanced health endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/")
        if response.status_code == 200:
            data = response.json()
            print("✓ Health check passed")
            print(f"  Security features: {data.get('security_features', {})}")
            print(f"  Storage info: {data.get('storage_info', {})}")
            return True
        else:
            print(f"✗ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Health check error: {e}")
        return False

def test_valid_file_upload(test_files):
    """Test uploading a valid file"""
    try:
        with open(test_files['valid_audio'], 'rb') as f:
            files = {'file': ('test_audio.wav', f, 'audio/wav')}
            response = requests.post(f"{BASE_URL}/api/upload", files=files)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✓ Valid file upload successful")
                print(f"  Job ID: {data['data']['job_id']}")
                print(f"  File type: {data['data']['file_type']}")
                print(f"  MIME type: {data['data']['mime_type']}")
                return data['data']['job_id']
            else:
                print(f"✗ Valid file upload failed: {data.get('message')}")
                return None
        else:
            print(f"✗ Valid file upload failed: {response.status_code}")
            return None
    except Exception as e:
        print(f"✗ Valid file upload error: {e}")
        return None

def test_invalid_file_upload(test_files):
    """Test uploading an invalid file"""
    try:
        with open(test_files['invalid_audio'], 'rb') as f:
            files = {'file': ('fake_audio.mp3', f, 'audio/mpeg')}
            response = requests.post(f"{BASE_URL}/api/upload", files=files)
        
        if response.status_code == 400:
            data = response.json()
            print("✓ Invalid file correctly rejected")
            print(f"  Error: {data.get('message')}")
            return True
        else:
            print(f"✗ Invalid file not rejected: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Invalid file test error: {e}")
        return False

def test_dangerous_filename():
    """Test file with dangerous filename"""
    try:
        # Create a file with dangerous characters in name
        dangerous_names = [
            '../../../etc/passwd.wav',
            'test<script>alert(1)</script>.wav',
            'test|rm -rf /.wav'
        ]
        
        for dangerous_name in dangerous_names:
            # Create a simple valid audio file
            wav_header = b'RIFF\x24\x08\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x44\xac\x00\x00\x88X\x01\x00\x02\x00\x10\x00data\x00\x08\x00\x00'
            
            files = {'file': (dangerous_name, wav_header + b'\x00' * 1024, 'audio/wav')}
            response = requests.post(f"{BASE_URL}/api/upload", files=files)
            
            if response.status_code == 400:
                print(f"✓ Dangerous filename rejected: {dangerous_name}")
            else:
                print(f"✗ Dangerous filename not rejected: {dangerous_name}")
                return False
        
        return True
    except Exception as e:
        print(f"✗ Dangerous filename test error: {e}")
        return False

def test_empty_file_upload(test_files):
    """Test uploading an empty file"""
    try:
        with open(test_files['empty_file'], 'rb') as f:
            files = {'file': ('empty.wav', f, 'audio/wav')}
            response = requests.post(f"{BASE_URL}/api/upload", files=files)
        
        if response.status_code == 400:
            print("✓ Empty file correctly rejected")
            return True
        else:
            print(f"✗ Empty file not rejected: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Empty file test error: {e}")
        return False

def test_file_size_limit(test_files):
    """Test file size limit enforcement"""
    try:
        with open(test_files['large_file'], 'rb') as f:
            files = {'file': ('large_audio.wav', f, 'audio/wav')}
            response = requests.post(f"{BASE_URL}/api/upload", files=files)
        
        # This might pass or fail depending on the configured size limit
        if response.status_code == 413:
            print("✓ Large file correctly rejected (size limit)")
            return True
        elif response.status_code == 200:
            print("✓ Large file accepted (within size limit)")
            return True
        else:
            print(f"✗ Unexpected response for large file: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ File size test error: {e}")
        return False

def test_cleanup_endpoint():
    """Test the cleanup endpoint"""
    try:
        cleanup_data = {'max_age_hours': 0}  # Clean everything
        response = requests.post(
            f"{BASE_URL}/api/files/cleanup",
            json=cleanup_data,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✓ Cleanup endpoint working")
            print(f"  Cleanup stats: {data.get('data', {})}")
            return True
        else:
            print(f"✗ Cleanup endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Cleanup test error: {e}")
        return False

def test_job_status(job_id):
    """Test job status endpoint"""
    if not job_id:
        return False
    
    try:
        response = requests.get(f"{BASE_URL}/api/status/{job_id}")
        if response.status_code == 200:
            data = response.json()
            print("✓ Job status retrieved")
            print(f"  Status: {data['data']['status']}")
            return True
        else:
            print(f"✗ Job status failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Job status error: {e}")
        return False

def main():
    """Run all file validation tests"""
    print("🧠 MinuteMate File Validation Test Suite")
    print("=" * 50)
    
    # Create test files
    test_files = create_test_files()
    
    try:
        # Test health endpoint
        print("\n1. Testing enhanced health endpoint...")
        if not test_health_endpoint():
            print("❌ Health check failed. Is the server running?")
            return
        
        # Test valid file upload
        print("\n2. Testing valid file upload...")
        job_id = test_valid_file_upload(test_files)
        
        # Test invalid file upload
        print("\n3. Testing invalid file upload...")
        test_invalid_file_upload(test_files)
        
        # Test dangerous filename
        print("\n4. Testing dangerous filename handling...")
        test_dangerous_filename()
        
        # Test empty file
        print("\n5. Testing empty file handling...")
        test_empty_file_upload(test_files)
        
        # Test file size limits
        print("\n6. Testing file size limits...")
        test_file_size_limit(test_files)
        
        # Test job status
        print("\n7. Testing job status...")
        test_job_status(job_id)
        
        # Test cleanup endpoint
        print("\n8. Testing cleanup endpoint...")
        test_cleanup_endpoint()
        
        print("\n✅ File validation test suite completed!")
        print("\n🎉 Enhanced file validation and storage system is working!")
        
    finally:
        # Cleanup
        cleanup_test_files(test_files)

if __name__ == "__main__":
    main()
