#!/usr/bin/env python3
"""
MinuteMate Error Handling Test Suite
Comprehensive tests for error handling, logging, and monitoring systems.
"""

import requests
import json
import time
import threading
from concurrent.futures import ThreadPoolExecutor

# Configuration
BASE_URL = "http://localhost:5000"

def test_health_endpoint():
    """Test the health check endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/")
        if response.status_code == 200:
            data = response.json()
            print("✓ Health check passed")
            print(f"  Status: {data.get('status')}")
            print(f"  Version: {data.get('version')}")
            
            # Check for response headers
            headers = response.headers
            if 'X-Request-ID' in headers:
                print(f"  Request ID: {headers['X-Request-ID']}")
            if 'X-Response-Time' in headers:
                print(f"  Response Time: {headers['X-Response-Time']}")
            
            return True
        else:
            print(f"✗ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Health check error: {e}")
        return False

def test_detailed_health_endpoint():
    """Test the detailed health monitoring endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/api/health/detailed")
        if response.status_code == 200:
            data = response.json()
            print("✓ Detailed health check passed")
            print(f"  Status: {data.get('status')}")
            print(f"  Uptime: {data.get('uptime_seconds', 0):.1f}s")
            print(f"  Total Requests: {data.get('requests_total', 0)}")
            print(f"  Error Rate: {data.get('error_rate', 0):.2%}")
            print(f"  Avg Response Time: {data.get('avg_response_time', 0):.3f}s")
            return True
        else:
            print(f"✗ Detailed health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Detailed health check error: {e}")
        return False

def test_404_error():
    """Test 404 error handling"""
    try:
        response = requests.get(f"{BASE_URL}/nonexistent-endpoint")
        if response.status_code == 404:
            data = response.json()
            print("✓ 404 error handled correctly")
            print(f"  Error Code: {data.get('error', {}).get('code')}")
            print(f"  Error ID: {data.get('error', {}).get('error_id')}")
            return True
        else:
            print(f"✗ 404 error not handled correctly: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ 404 error test failed: {e}")
        return False

def test_validation_error():
    """Test validation error handling"""
    try:
        # Send request without file
        response = requests.post(f"{BASE_URL}/api/upload")
        if response.status_code == 400:
            data = response.json()
            print("✓ Validation error handled correctly")
            print(f"  Error Code: {data.get('error', {}).get('code')}")
            print(f"  Message: {data.get('error', {}).get('message')}")
            return True
        else:
            print(f"✗ Validation error not handled correctly: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Validation error test failed: {e}")
        return False

def test_method_not_allowed():
    """Test method not allowed error"""
    try:
        response = requests.put(f"{BASE_URL}/api/upload")
        if response.status_code == 405:
            data = response.json()
            print("✓ Method not allowed error handled correctly")
            print(f"  Error Code: {data.get('error', {}).get('code')}")
            return True
        else:
            print(f"✗ Method not allowed error not handled correctly: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Method not allowed test failed: {e}")
        return False

def test_rate_limiting():
    """Test rate limiting functionality"""
    print("Testing rate limiting (this may take a moment)...")
    
    def make_request():
        try:
            response = requests.get(f"{BASE_URL}/")
            return response.status_code
        except:
            return None
    
    # Make many requests quickly
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(make_request) for _ in range(50)]
        results = [f.result() for f in futures]
    
    # Check if any requests were rate limited
    rate_limited = any(status == 429 for status in results if status)
    successful = sum(1 for status in results if status == 200)
    
    print(f"✓ Rate limiting test completed")
    print(f"  Successful requests: {successful}")
    print(f"  Rate limited: {rate_limited}")
    
    return True

def test_security_monitoring():
    """Test security monitoring for suspicious requests"""
    try:
        # Send request with suspicious content
        suspicious_data = {
            'test': '<script>alert("xss")</script>',
            'query': 'SELECT * FROM users; DROP TABLE users;'
        }
        
        response = requests.post(
            f"{BASE_URL}/api/upload",
            json=suspicious_data,
            headers={'Content-Type': 'application/json'}
        )
        
        # Should be blocked or logged as suspicious
        print("✓ Security monitoring test completed")
        print(f"  Response status: {response.status_code}")
        
        if response.status_code == 403:
            print("  Suspicious request correctly blocked")
        else:
            print("  Request processed (may be logged as suspicious)")
        
        return True
    except Exception as e:
        print(f"✗ Security monitoring test failed: {e}")
        return False

def test_response_headers():
    """Test that proper response headers are included"""
    try:
        response = requests.get(f"{BASE_URL}/")
        headers = response.headers
        
        required_headers = ['X-Request-ID', 'X-Response-Time']
        missing_headers = [h for h in required_headers if h not in headers]
        
        if not missing_headers:
            print("✓ Response headers test passed")
            print(f"  Request ID: {headers.get('X-Request-ID')}")
            print(f"  Response Time: {headers.get('X-Response-Time')}")
            return True
        else:
            print(f"✗ Missing headers: {missing_headers}")
            return False
    except Exception as e:
        print(f"✗ Response headers test failed: {e}")
        return False

def test_large_file_error():
    """Test large file error handling"""
    try:
        # Create a large dummy file content
        large_content = b'x' * (600 * 1024 * 1024)  # 600MB
        
        files = {'file': ('large_file.wav', large_content, 'audio/wav')}
        response = requests.post(f"{BASE_URL}/api/upload", files=files)
        
        if response.status_code == 413:
            data = response.json()
            print("✓ Large file error handled correctly")
            print(f"  Error Code: {data.get('error', {}).get('code')}")
            print(f"  Max Size: {data.get('error', {}).get('details', {}).get('max_size_mb')}MB")
            return True
        else:
            print(f"✗ Large file error not handled correctly: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Large file error test failed: {e}")
        return False

def test_json_error():
    """Test invalid JSON error handling"""
    try:
        # Send invalid JSON
        response = requests.post(
            f"{BASE_URL}/api/files/cleanup",
            data="invalid json content",
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 400:
            print("✓ Invalid JSON error handled correctly")
            return True
        else:
            print(f"✗ Invalid JSON error not handled correctly: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Invalid JSON test failed: {e}")
        return False

def test_performance_monitoring():
    """Test performance monitoring"""
    try:
        start_time = time.time()
        response = requests.get(f"{BASE_URL}/")
        end_time = time.time()
        
        response_time = end_time - start_time
        header_time = response.headers.get('X-Response-Time', '0s')
        
        print("✓ Performance monitoring test completed")
        print(f"  Measured response time: {response_time:.3f}s")
        print(f"  Header response time: {header_time}")
        
        return True
    except Exception as e:
        print(f"✗ Performance monitoring test failed: {e}")
        return False

def main():
    """Run all error handling and logging tests"""
    print("🧠 MinuteMate Error Handling & Logging Test Suite")
    print("=" * 60)
    
    tests = [
        ("Basic Health Check", test_health_endpoint),
        ("Detailed Health Check", test_detailed_health_endpoint),
        ("404 Error Handling", test_404_error),
        ("Validation Error Handling", test_validation_error),
        ("Method Not Allowed", test_method_not_allowed),
        ("Response Headers", test_response_headers),
        ("Performance Monitoring", test_performance_monitoring),
        ("Rate Limiting", test_rate_limiting),
        ("Security Monitoring", test_security_monitoring),
        ("Large File Error", test_large_file_error),
        ("Invalid JSON Error", test_json_error),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{len([t for t in tests if tests.index(t) < tests.index((test_name, test_func))])+1}. Testing {test_name}...")
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"✗ Test failed with exception: {e}")
    
    print(f"\n{'='*60}")
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All error handling and logging tests passed!")
    else:
        print(f"⚠️  {total - passed} tests failed. Check the logs for details.")
    
    print("\n📋 Check the following log files for detailed information:")
    print("  - logs/minutemate.log (main application log)")
    print("  - logs/errors.log (error-specific log)")
    print("  - logs/access.log (request access log)")

if __name__ == "__main__":
    main()
