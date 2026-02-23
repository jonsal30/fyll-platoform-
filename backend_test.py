import requests
import sys
from datetime import datetime

class TimeClockAPITester:
    def __init__(self, base_url="https://workforce-tracker-52.preview.emergentagent.com"):
        self.base_url = base_url
        self.session_token = "test_session_admin_001"  # Pre-created test token
        self.numeric_id = "1234"  # Test numeric ID
        self.tests_run = 0
        self.tests_passed = 0

    def run_test(self, name, method, endpoint, expected_status, data=None, use_auth=True):
        """Run a single API test"""
        url = f"{self.base_url}/api/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if use_auth and self.session_token:
            headers['Authorization'] = f'Bearer {self.session_token}'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                if response.content:
                    try:
                        json_data = response.json()
                        print(f"   Response keys: {list(json_data.keys()) if isinstance(json_data, dict) else 'Non-dict response'}")
                    except:
                        print(f"   Response: {response.text[:100]}...")
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                if response.content:
                    print(f"   Error: {response.text[:200]}")

            return success, response.json() if success and response.content else {}

        except Exception as e:
            print(f"❌ Failed - Network Error: {str(e)}")
            return False, {}

    def test_numeric_login(self):
        """Test numeric ID login"""
        success, response = self.run_test(
            "Numeric Login", 
            "POST", 
            "auth/numeric-login", 
            200,
            data={"numeric_id": self.numeric_id},
            use_auth=False
        )
        return success

    def test_auth_me(self):
        """Test /api/auth/me endpoint"""
        success, response = self.run_test(
            "Auth Me", 
            "GET", 
            "auth/me", 
            200
        )
        return success, response

    def test_sites(self):
        """Test /api/sites endpoint"""
        success, response = self.run_test(
            "Get Sites", 
            "GET", 
            "sites", 
            200
        )
        return success, response

    def test_clock_status(self):
        """Test /api/clock/status endpoint"""
        success, response = self.run_test(
            "Clock Status", 
            "GET", 
            "clock/status", 
            200
        )
        return success, response

    def test_api_root(self):
        """Test API root endpoint"""
        success, response = self.run_test(
            "API Root", 
            "GET", 
            "", 
            200,
            use_auth=False
        )
        return success

def main():
    print("🚀 Starting Time Clock API Tests...")
    print("=" * 50)
    
    tester = TimeClockAPITester()

    # Test API root (no auth needed)
    print("\n📋 Testing Basic API Access...")
    tester.test_api_root()

    # Test numeric login
    print("\n📋 Testing Authentication...")
    login_success = tester.test_numeric_login()
    
    if not login_success:
        print("⚠️  Numeric login failed, but continuing with pre-created session token...")

    # Test protected endpoints with session token
    print("\n📋 Testing Protected Endpoints...")
    auth_success, user_data = tester.test_auth_me()
    
    if not auth_success:
        print("❌ Authentication failed - stopping tests")
        return 1

    sites_success, sites_data = tester.test_sites()
    status_success, status_data = tester.test_clock_status()

    # Print test summary
    print("\n" + "=" * 50)
    print(f"📊 Test Summary: {tester.tests_passed}/{tester.tests_run} passed")
    
    if auth_success and user_data:
        print(f"👤 Test User: {user_data.get('name', 'Unknown')} ({user_data.get('role', 'Unknown')})")
    
    if sites_success and isinstance(sites_data, list):
        print(f"🏢 Sites Available: {len(sites_data)}")
    
    if status_success and status_data:
        print(f"⏰ Clock Status: {'Clocked In' if status_data.get('is_clocked_in') else 'Not Clocked In'}")

    # Return status
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)