#!/usr/bin/env python3
"""
Test the login UI functionality
"""

import requests

BASE_URL = "http://localhost:8001"

def test_login_page():
    """Test if login page loads"""
    print("Testing login page...")
    response = requests.get(f"{BASE_URL}/login")
    if response.status_code == 200:
        print("✓ Login page loads successfully")
        if "Traffic Violation System" in response.text:
            print("✓ Login page content is correct")
        return True
    else:
        print(f"✗ Login page failed to load: {response.status_code}")
        return False

def test_static_files():
    """Test if static files are accessible"""
    print("\nTesting static files...")
    
    files = [
        ("/static/login.css", "login-container"),
        ("/static/auth.js", "AuthManager"),
        ("/static/login.js", "loginForm")
    ]
    
    for file_path, expected_content in files:
        response = requests.get(f"{BASE_URL}{file_path}")
        if response.status_code == 200 and expected_content in response.text:
            print(f"✓ {file_path} loads successfully")
        else:
            print(f"✗ {file_path} failed to load")

def test_api_login():
    """Test API login endpoint"""
    print("\nTesting API login...")
    
    # Test successful login
    data = {
        "username": "admin",
        "password": "admin123",
        "grant_type": "password"
    }
    
    response = requests.post(f"{BASE_URL}/api/auth/login", data=data)
    if response.status_code == 200:
        token_data = response.json()
        if "access_token" in token_data:
            print("✓ API login works successfully")
            print(f"  Token: {token_data['access_token'][:50]}...")
            return token_data['access_token']
        else:
            print("✗ API login response missing token")
    else:
        print(f"✗ API login failed: {response.status_code}")
    
    return None

def test_auth_endpoints(token):
    """Test authenticated endpoints"""
    print("\nTesting authenticated endpoints...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test /api/auth/me
    response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
    if response.status_code == 200:
        user_data = response.json()
        print("✓ /api/auth/me works successfully")
        print(f"  User: {user_data['username']} ({user_data['role']})")
    else:
        print(f"✗ /api/auth/me failed: {response.status_code}")

def main():
    print("=" * 60)
    print("Testing Login UI and Authentication")
    print("=" * 60)
    
    # Test login page
    if test_login_page():
        # Test static files
        test_static_files()
        
        # Test API login
        token = test_api_login()
        
        if token:
            # Test authenticated endpoints
            test_auth_endpoints(token)
    
    print("\n" + "=" * 60)
    print("Login UI tests completed!")
    print("=" * 60)
    print("\nTo test in browser, visit: http://localhost:8001/login")
    print("Quick login buttons are available for all three roles.")

if __name__ == "__main__":
    main()