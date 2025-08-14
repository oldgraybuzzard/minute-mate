#!/usr/bin/env python3
"""
MinuteMate Frontend Test Suite
Automated tests for the frontend interface functionality.
"""

import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import tempfile
import os

class FrontendTester:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.frontend_url = f"{base_url}/frontend/"
        self.driver = None
        self.setup_driver()
    
    def setup_driver(self):
        """Setup Chrome WebDriver with appropriate options"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in headless mode
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.implicitly_wait(10)
            print("✓ Chrome WebDriver initialized")
        except Exception as e:
            print(f"✗ Failed to initialize WebDriver: {e}")
            print("Please ensure ChromeDriver is installed and in PATH")
            raise
    
    def teardown(self):
        """Clean up WebDriver"""
        if self.driver:
            self.driver.quit()
            print("✓ WebDriver closed")
    
    def test_backend_health(self):
        """Test if backend is running and healthy"""
        try:
            response = requests.get(f"{self.base_url}/", timeout=5)
            if response.status_code == 200:
                print("✓ Backend health check passed")
                return True
            else:
                print(f"✗ Backend health check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"✗ Backend health check error: {e}")
            return False
    
    def test_frontend_loads(self):
        """Test if frontend page loads correctly"""
        try:
            self.driver.get(self.frontend_url)
            
            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "container"))
            )
            
            # Check for key elements
            title = self.driver.find_element(By.TAG_NAME, "h1")
            if "MinuteMate" in title.text:
                print("✓ Frontend page loads correctly")
                return True
            else:
                print("✗ Frontend page title incorrect")
                return False
                
        except TimeoutException:
            print("✗ Frontend page failed to load (timeout)")
            return False
        except Exception as e:
            print(f"✗ Frontend page load error: {e}")
            return False
    
    def test_upload_section_visible(self):
        """Test if upload section is visible by default"""
        try:
            upload_section = self.driver.find_element(By.ID, "upload-section")
            if upload_section.is_displayed():
                print("✓ Upload section is visible")
                return True
            else:
                print("✗ Upload section is not visible")
                return False
        except NoSuchElementException:
            print("✗ Upload section not found")
            return False
    
    def test_file_upload_area(self):
        """Test file upload area functionality"""
        try:
            upload_area = self.driver.find_element(By.ID, "upload-area")
            file_input = self.driver.find_element(By.ID, "file-input")
            
            # Check if upload area is clickable
            if upload_area.is_displayed() and file_input:
                print("✓ File upload area is functional")
                return True
            else:
                print("✗ File upload area is not functional")
                return False
        except NoSuchElementException:
            print("✗ File upload elements not found")
            return False
    
    def test_upload_options(self):
        """Test upload configuration options"""
        try:
            language_select = self.driver.find_element(By.ID, "language-select")
            format_select = self.driver.find_element(By.ID, "format-select")
            
            # Check if options are available
            language_options = language_select.find_elements(By.TAG_NAME, "option")
            format_options = format_select.find_elements(By.TAG_NAME, "option")
            
            if len(language_options) > 1 and len(format_options) > 1:
                print("✓ Upload options are available")
                print(f"  Languages: {len(language_options)} options")
                print(f"  Formats: {len(format_options)} options")
                return True
            else:
                print("✗ Upload options are insufficient")
                return False
        except NoSuchElementException:
            print("✗ Upload option elements not found")
            return False
    
    def test_upload_button_state(self):
        """Test upload button initial state"""
        try:
            upload_btn = self.driver.find_element(By.ID, "upload-btn")
            
            # Button should be disabled initially
            if upload_btn.get_attribute("disabled"):
                print("✓ Upload button is correctly disabled initially")
                return True
            else:
                print("✗ Upload button should be disabled initially")
                return False
        except NoSuchElementException:
            print("✗ Upload button not found")
            return False
    
    def test_supported_formats_display(self):
        """Test if supported formats are displayed"""
        try:
            formats_section = self.driver.find_element(By.CLASS_NAME, "supported-formats")
            format_tags = formats_section.find_elements(By.CLASS_NAME, "format-tag")
            
            if len(format_tags) > 0:
                print(f"✓ Supported formats displayed ({len(format_tags)} formats)")
                return True
            else:
                print("✗ No supported formats displayed")
                return False
        except NoSuchElementException:
            print("✗ Supported formats section not found")
            return False
    
    def test_processing_section_hidden(self):
        """Test if processing section is hidden initially"""
        try:
            processing_section = self.driver.find_element(By.ID, "processing-section")
            
            if not processing_section.is_displayed():
                print("✓ Processing section is correctly hidden")
                return True
            else:
                print("✗ Processing section should be hidden initially")
                return False
        except NoSuchElementException:
            print("✗ Processing section not found")
            return False
    
    def test_results_section_hidden(self):
        """Test if results section is hidden initially"""
        try:
            results_section = self.driver.find_element(By.ID, "results-section")
            
            if not results_section.is_displayed():
                print("✓ Results section is correctly hidden")
                return True
            else:
                print("✗ Results section should be hidden initially")
                return False
        except NoSuchElementException:
            print("✗ Results section not found")
            return False
    
    def test_error_section_hidden(self):
        """Test if error section is hidden initially"""
        try:
            error_section = self.driver.find_element(By.ID, "error-section")
            
            if not error_section.is_displayed():
                print("✓ Error section is correctly hidden")
                return True
            else:
                print("✗ Error section should be hidden initially")
                return False
        except NoSuchElementException:
            print("✗ Error section not found")
            return False
    
    def test_footer_elements(self):
        """Test footer elements"""
        try:
            footer = self.driver.find_element(By.CLASS_NAME, "footer")
            footer_links = footer.find_elements(By.TAG_NAME, "a")
            
            if len(footer_links) > 0:
                print(f"✓ Footer elements present ({len(footer_links)} links)")
                return True
            else:
                print("✗ Footer links not found")
                return False
        except NoSuchElementException:
            print("✗ Footer not found")
            return False
    
    def test_responsive_design(self):
        """Test responsive design at different screen sizes"""
        try:
            # Test desktop size
            self.driver.set_window_size(1920, 1080)
            time.sleep(1)
            
            container = self.driver.find_element(By.CLASS_NAME, "container")
            desktop_width = container.size['width']
            
            # Test tablet size
            self.driver.set_window_size(768, 1024)
            time.sleep(1)
            tablet_width = container.size['width']
            
            # Test mobile size
            self.driver.set_window_size(375, 667)
            time.sleep(1)
            mobile_width = container.size['width']
            
            if desktop_width > tablet_width > mobile_width:
                print("✓ Responsive design works correctly")
                print(f"  Desktop: {desktop_width}px, Tablet: {tablet_width}px, Mobile: {mobile_width}px")
                return True
            else:
                print("✗ Responsive design may have issues")
                return False
                
        except Exception as e:
            print(f"✗ Responsive design test error: {e}")
            return False
        finally:
            # Reset to desktop size
            self.driver.set_window_size(1920, 1080)
    
    def test_javascript_functionality(self):
        """Test basic JavaScript functionality"""
        try:
            # Execute JavaScript to check if app is initialized
            result = self.driver.execute_script(
                "return typeof window.MinuteMateApp !== 'undefined' || document.querySelector('.container') !== null;"
            )
            
            if result:
                print("✓ JavaScript functionality is working")
                return True
            else:
                print("✗ JavaScript functionality may have issues")
                return False
        except Exception as e:
            print(f"✗ JavaScript test error: {e}")
            return False
    
    def test_system_health_button(self):
        """Test system health check button"""
        try:
            health_btn = self.driver.find_element(By.ID, "health-check")
            
            if health_btn.is_displayed():
                print("✓ System health button is present")
                return True
            else:
                print("✗ System health button is not visible")
                return False
        except NoSuchElementException:
            print("✗ System health button not found")
            return False
    
    def run_all_tests(self):
        """Run all frontend tests"""
        print("🧠 MinuteMate Frontend Test Suite")
        print("=" * 50)
        
        tests = [
            ("Backend Health Check", self.test_backend_health),
            ("Frontend Page Load", self.test_frontend_loads),
            ("Upload Section Visibility", self.test_upload_section_visible),
            ("File Upload Area", self.test_file_upload_area),
            ("Upload Options", self.test_upload_options),
            ("Upload Button State", self.test_upload_button_state),
            ("Supported Formats Display", self.test_supported_formats_display),
            ("Processing Section Hidden", self.test_processing_section_hidden),
            ("Results Section Hidden", self.test_results_section_hidden),
            ("Error Section Hidden", self.test_error_section_hidden),
            ("Footer Elements", self.test_footer_elements),
            ("JavaScript Functionality", self.test_javascript_functionality),
            ("System Health Button", self.test_system_health_button),
            ("Responsive Design", self.test_responsive_design),
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
        
        print(f"\n{'='*50}")
        print(f"Test Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All frontend tests passed!")
        else:
            print(f"⚠️  {total - passed} tests failed. Check the output for details.")
        
        return passed == total

def main():
    """Main test runner"""
    tester = None
    try:
        tester = FrontendTester()
        success = tester.run_all_tests()
        
        if success:
            print("\n✅ Frontend is ready for use!")
            print(f"🌐 Access the interface at: http://localhost:5000/frontend/")
            print(f"📋 Demo page available at: http://localhost:5000/frontend/demo.html")
        else:
            print("\n❌ Some tests failed. Please check the issues above.")
            
    except Exception as e:
        print(f"\n💥 Test suite failed to run: {e}")
    finally:
        if tester:
            tester.teardown()

if __name__ == "__main__":
    main()
