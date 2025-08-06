#!/usr/bin/env python3
"""Test script to verify dashboard authentication and navigation"""

import requests
import json

BASE_URL = "http://localhost:8001"

def test_login(username, password):
    """Test login and return token"""
    print(f"\nTesting login for {username}...")
    
    # Prepare form data
    data = {
        'username': username,
        'password': password,
        'grant_type': 'password'
    }
    
    response = requests.post(f"{BASE_URL}/api/auth/login", data=data)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✓ Login successful! Token: {result['access_token'][:20]}...")
        return result['access_token']
    else:
        print(f"✗ Login failed: {response.status_code} - {response.text}")
        return None

def test_dashboard_access(token, dashboard_path, role):
    """Test accessing a dashboard with authentication"""
    print(f"\nTesting {role} dashboard access at {dashboard_path}...")
    
    headers = {
        'Authorization': f'Bearer {token}'
    }
    
    response = requests.get(f"{BASE_URL}{dashboard_path}", headers=headers)
    
    if response.status_code == 200:
        # Check if it's HTML content
        if 'text/html' in response.headers.get('content-type', ''):
            print(f"✓ Dashboard accessible! Response contains HTML")
            # Check for specific dashboard content
            if f"{role} Dashboard" in response.text:
                print(f"✓ Correct {role} dashboard loaded")
            else:
                print(f"⚠ Dashboard loaded but might not be the correct one")
        else:
            print(f"✗ Unexpected content type: {response.headers.get('content-type')}")
    else:
        print(f"✗ Dashboard access failed: {response.status_code}")

def test_api_access(token, endpoint):
    """Test API endpoint access with authentication"""
    print(f"\nTesting API access at {endpoint}...")
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    response = requests.get(f"{BASE_URL}{endpoint}", headers=headers)
    
    if response.status_code == 200:
        print(f"✓ API accessible! Response: {json.dumps(response.json(), indent=2)[:100]}...")
    else:
        print(f"✗ API access failed: {response.status_code} - {response.text}")

def main():
    print("=== Traffic Violation System Dashboard Test ===")
    
    # Test credentials
    test_cases = [
        ("officer1", "officer123", "/officer/dashboard", "Officer"),
        ("cashier1", "cashier123", "/cashier/dashboard", "Cashier"),
        ("admin", "admin123", "/admin/dashboard", "Admin")
    ]
    
    for username, password, dashboard, role in test_cases:
        print(f"\n{'='*50}")
        print(f"Testing {role} User: {username}")
        print('='*50)
        
        # Test login
        token = test_login(username, password)
        
        if token:
            # Test dashboard access
            test_dashboard_access(token, dashboard, role)
            
            # Test API access
            test_api_access(token, "/api/auth/me")
            
            # Test role-specific endpoints
            if role == "Officer":
                test_api_access(token, "/api/violation-types")
            elif role == "Cashier":
                test_api_access(token, "/api/violations?limit=5")
            elif role == "Admin":
                test_api_access(token, "/api/users")

if __name__ == "__main__":
    main()