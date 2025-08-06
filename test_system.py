#!/usr/bin/env python3
"""Test the complete system functionality"""

import requests
import json
import time

BASE_URL = "http://localhost:8001"

def test_login(username, password):
    """Test user login"""
    print(f"\n🔐 Testing login for {username}...")
    
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        data={"username": username, "password": password}
    )
    
    if response.status_code == 200:
        token = response.json()["access_token"]
        print(f"✅ Login successful! Token: {token[:50]}...")
        return token
    else:
        print(f"❌ Login failed: {response.status_code}")
        return None

def test_dashboard_stats(token, user_type):
    """Test dashboard statistics"""
    print(f"\n📊 Testing dashboard stats for {user_type}...")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/dashboard/statistics", headers=headers)
    
    if response.status_code == 200:
        stats = response.json()
        print(f"✅ Dashboard stats retrieved:")
        for key, value in stats.items():
            print(f"   - {key}: {value}")
    else:
        print(f"❌ Failed to get stats: {response.status_code}")

def test_create_violation(token):
    """Test creating a violation as officer"""
    print("\n🚨 Testing violation creation...")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    violation_data = {
        "plate_number": "ABC-1234",
        "violation_type_id": 1,
        "location": "Main Street & 5th Avenue",
        "description": "Vehicle was speeding - 80mph in 60mph zone"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/violations",
        headers=headers,
        json=violation_data
    )
    
    if response.status_code == 200:
        violation = response.json()
        print(f"✅ Violation created successfully!")
        print(f"   - Ticket: {violation['ticket_number']}")
        print(f"   - Fine: ${violation['fine_amount']}")
        print(f"   - Status: {violation['status']}")
        return violation['ticket_number']
    else:
        print(f"❌ Failed to create violation: {response.status_code}")
        print(f"   Response: {response.text}")
        return None

def test_search_violation(token, ticket_number):
    """Test searching for a violation"""
    print(f"\n🔍 Testing violation search for {ticket_number}...")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{BASE_URL}/api/violations/ticket/{ticket_number}",
        headers=headers
    )
    
    if response.status_code == 200:
        violation = response.json()
        print(f"✅ Violation found!")
        print(f"   - Ticket: {violation['ticket_number']}")
        print(f"   - Fine: ${violation['fine_amount']}")
        print(f"   - Status: {violation['status']}")
        return violation['id']
    else:
        print(f"❌ Failed to find violation: {response.status_code}")
        return None

def test_process_payment(token, violation_id):
    """Test processing a payment as cashier"""
    print(f"\n💰 Testing payment processing for violation ID {violation_id}...")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    payment_data = {
        "violation_id": violation_id,
        "payment_method": "cash",
        "transaction_reference": "CASH-12345",
        "notes": "Paid in full at counter"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/payments",
        headers=headers,
        json=payment_data
    )
    
    if response.status_code == 200:
        payment = response.json()
        print(f"✅ Payment processed successfully!")
        print(f"   - Receipt: {payment['receipt_number']}")
        print(f"   - Amount: ${payment['amount']}")
        print(f"   - Method: {payment['payment_method']}")
    else:
        print(f"❌ Failed to process payment: {response.status_code}")
        print(f"   Response: {response.text}")

def test_user_management(token):
    """Test user management as admin"""
    print("\n👥 Testing user management...")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/users", headers=headers)
    
    if response.status_code == 200:
        users = response.json()
        print(f"✅ Retrieved {len(users)} users:")
        for user in users:
            status = "Active" if user['is_active'] else "Inactive"
            print(f"   - {user['username']} ({user['role']}) - {status}")
    else:
        print(f"❌ Failed to get users: {response.status_code}")

def test_violations_list(token):
    """Test listing violations"""
    print("\n📋 Testing violations list...")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/violations?limit=5", headers=headers)
    
    if response.status_code == 200:
        violations = response.json()
        print(f"✅ Retrieved {len(violations)} violations:")
        for v in violations[:3]:  # Show first 3
            print(f"   - {v['ticket_number']} | {v['plate_number']} | ${v['fine_amount']} | {v['status']}")
    else:
        print(f"❌ Failed to get violations: {response.status_code}")

def main():
    print("=" * 60)
    print("Testing Traffic Violation Management System")
    print("=" * 60)
    
    # Test 1: Officer workflow
    print("\n### OFFICER WORKFLOW ###")
    officer_token = test_login("officer1", "officer123")
    if officer_token:
        test_dashboard_stats(officer_token, "Officer")
        ticket_number = test_create_violation(officer_token)
        test_violations_list(officer_token)
    
    # Test 2: Cashier workflow
    print("\n\n### CASHIER WORKFLOW ###")
    cashier_token = test_login("cashier1", "cashier123")
    if cashier_token and ticket_number:
        test_dashboard_stats(cashier_token, "Cashier")
        violation_id = test_search_violation(cashier_token, ticket_number)
        if violation_id:
            test_process_payment(cashier_token, violation_id)
    
    # Test 3: Admin workflow
    print("\n\n### ADMIN WORKFLOW ###")
    admin_token = test_login("admin", "admin123")
    if admin_token:
        test_dashboard_stats(admin_token, "Admin")
        test_user_management(admin_token)
        test_violations_list(admin_token)
    
    print("\n" + "=" * 60)
    print("Testing completed!")
    print("=" * 60)

if __name__ == "__main__":
    main()