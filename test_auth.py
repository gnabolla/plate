#!/usr/bin/env python3
"""
Test authentication system functionality
"""

import requests
import json

BASE_URL = "http://localhost:8001"

def test_login(username, password):
    """Test login endpoint"""
    print(f"\nTesting login for user: {username}")
    
    # Prepare form data for OAuth2PasswordRequestForm
    data = {
        "username": username,
        "password": password,
        "grant_type": "password"
    }
    
    response = requests.post(f"{BASE_URL}/api/auth/login", data=data)
    
    if response.status_code == 200:
        token_data = response.json()
        print(f"✓ Login successful!")
        print(f"  Access token: {token_data['access_token'][:50]}...")
        return token_data['access_token']
    else:
        print(f"✗ Login failed: {response.status_code}")
        print(f"  Error: {response.json()}")
        return None

def test_get_current_user(token):
    """Test getting current user info"""
    print("\nTesting get current user...")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
    
    if response.status_code == 200:
        user_data = response.json()
        print(f"✓ Got user info successfully!")
        print(f"  Username: {user_data['username']}")
        print(f"  Role: {user_data['role']}")
        print(f"  Email: {user_data['email']}")
        return user_data
    else:
        print(f"✗ Failed to get user info: {response.status_code}")
        print(f"  Error: {response.json()}")
        return None

def test_list_users(token):
    """Test listing users (super admin only)"""
    print("\nTesting list users...")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/users", headers=headers)
    
    if response.status_code == 200:
        users = response.json()
        print(f"✓ Listed users successfully!")
        print(f"  Total users: {len(users)}")
        for user in users:
            print(f"  - {user['username']} ({user['role']})")
    else:
        print(f"✗ Failed to list users: {response.status_code}")
        print(f"  Error: {response.json()}")

def test_unauthorized_access():
    """Test accessing protected endpoint without token"""
    print("\nTesting unauthorized access...")
    
    response = requests.get(f"{BASE_URL}/api/auth/me")
    
    if response.status_code == 401:
        print("✓ Correctly rejected unauthorized request")
    else:
        print(f"✗ Unexpected response: {response.status_code}")

def main():
    """Run all tests"""
    print("=" * 60)
    print("Testing Traffic Violation Management System Authentication")
    print("=" * 60)
    
    # Test unauthorized access
    test_unauthorized_access()
    
    # Test login with different users
    users = [
        ("admin", "admin123"),
        ("officer1", "officer123"),
        ("cashier1", "cashier123"),
        ("invalid", "wrongpass")
    ]
    
    for username, password in users:
        token = test_login(username, password)
        
        if token:
            # Test getting current user
            user_data = test_get_current_user(token)
            
            # Test listing users (should only work for admin)
            if user_data and username == "admin":
                test_list_users(token)
            elif user_data and username != "admin":
                # Test that non-admins can't list users
                print("\nTesting that non-admin can't list users...")
                headers = {"Authorization": f"Bearer {token}"}
                response = requests.get(f"{BASE_URL}/api/users", headers=headers)
                if response.status_code == 403:
                    print("✓ Correctly denied access to non-admin")
                else:
                    print(f"✗ Unexpected response: {response.status_code}")
    
    print("\n" + "=" * 60)
    print("Authentication tests completed!")
    print("=" * 60)

if __name__ == "__main__":
    main()