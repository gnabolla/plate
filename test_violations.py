#!/usr/bin/env python3
"""
Test violation management and payment processing functionality
"""

import requests
import json

BASE_URL = "http://localhost:8001"

# Store tokens for different users
tokens = {}

def login(username, password):
    """Login and get token"""
    data = {
        "username": username,
        "password": password,
        "grant_type": "password"
    }
    response = requests.post(f"{BASE_URL}/api/auth/login", data=data)
    if response.status_code == 200:
        token = response.json()["access_token"]
        tokens[username] = token
        return token
    return None

def test_violation_types():
    """Test violation type endpoints"""
    print("\n=== Testing Violation Types ===")
    
    # Get violation types (public endpoint)
    response = requests.get(f"{BASE_URL}/api/violation-types")
    if response.status_code == 200:
        types = response.json()
        print(f"✓ Found {len(types)} violation types")
        for vt in types[:3]:  # Show first 3
            print(f"  - {vt['code']}: {vt['name']} (₱{vt['fine_amount']})")
        return types
    else:
        print(f"✗ Failed to get violation types: {response.status_code}")
        return []

def test_create_violation(officer_token, vehicle_id, violation_type_id):
    """Test creating a violation"""
    print("\n=== Testing Violation Creation ===")
    
    headers = {"Authorization": f"Bearer {officer_token}"}
    violation_data = {
        "vehicle_id": vehicle_id,
        "violation_type_id": violation_type_id,
        "location": "EDSA Corner Ayala Avenue",
        "latitude": 14.5547,
        "longitude": 121.0244,
        "description": "Vehicle caught overspeeding at 120 km/h in 60 km/h zone",
        "fine_amount": 500.00
    }
    
    response = requests.post(
        f"{BASE_URL}/api/violations",
        json=violation_data,
        headers=headers
    )
    
    if response.status_code == 200:
        violation = response.json()
        print(f"✓ Created violation successfully!")
        print(f"  Ticket Number: {violation['ticket_number']}")
        print(f"  Fine Amount: ₱{violation['fine_amount']}")
        print(f"  Status: {violation['status']}")
        print(f"  Due Date: {violation['due_date']}")
        return violation
    else:
        print(f"✗ Failed to create violation: {response.status_code}")
        print(f"  Error: {response.json()}")
        return None

def test_list_violations(token, role):
    """Test listing violations"""
    print(f"\n=== Testing List Violations ({role}) ===")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/violations", headers=headers)
    
    if response.status_code == 200:
        violations = response.json()
        print(f"✓ Found {len(violations)} violations")
        for v in violations[:3]:  # Show first 3
            print(f"  - {v['ticket_number']}: {v['status']} (₱{v['fine_amount']})")
        return violations
    else:
        print(f"✗ Failed to list violations: {response.status_code}")
        return []

def test_process_payment(cashier_token, violation_id, amount):
    """Test processing a payment"""
    print("\n=== Testing Payment Processing ===")
    
    headers = {"Authorization": f"Bearer {cashier_token}"}
    payment_data = {
        "violation_id": violation_id,
        "amount": amount,
        "payment_method": "cash",
        "reference_number": None
    }
    
    response = requests.post(
        f"{BASE_URL}/api/payments",
        json=payment_data,
        headers=headers
    )
    
    if response.status_code == 200:
        payment = response.json()
        print(f"✓ Payment processed successfully!")
        print(f"  Transaction ID: {payment['transaction_id']}")
        print(f"  Receipt Number: {payment['receipt_number']}")
        print(f"  Amount: ₱{payment['amount']}")
        print(f"  Status: {payment['status']}")
        return payment
    else:
        print(f"✗ Failed to process payment: {response.status_code}")
        print(f"  Error: {response.json()}")
        return None

def test_dashboard_stats(token, role):
    """Test dashboard statistics"""
    print(f"\n=== Testing Dashboard Statistics ({role}) ===")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/dashboard/statistics", headers=headers)
    
    if response.status_code == 200:
        stats = response.json()
        print(f"✓ Got dashboard statistics:")
        for key, value in stats.items():
            print(f"  - {key}: {value}")
    else:
        print(f"✗ Failed to get statistics: {response.status_code}")

def test_get_violation_by_ticket(ticket_number):
    """Test getting violation by ticket number (public endpoint)"""
    print(f"\n=== Testing Get Violation by Ticket Number ===")
    
    response = requests.get(f"{BASE_URL}/api/violations/ticket/{ticket_number}")
    
    if response.status_code == 200:
        violation = response.json()
        print(f"✓ Found violation:")
        print(f"  Vehicle ID: {violation.get('vehicle_id', 'N/A')}")
        print(f"  Fine Amount: ₱{violation['fine_amount']}")
        print(f"  Status: {violation['status']}")
        return violation
    else:
        print(f"✗ Violation not found: {response.status_code}")
        return None

def main():
    """Run all tests"""
    print("=" * 60)
    print("Testing Traffic Violation Management System")
    print("=" * 60)
    
    # Login as different users
    print("\n=== Logging in users ===")
    admin_token = login("admin", "admin123")
    officer_token = login("officer1", "officer123")
    cashier_token = login("cashier1", "cashier123")
    
    if not all([admin_token, officer_token, cashier_token]):
        print("Failed to login all users!")
        return
    
    print("✓ All users logged in successfully")
    
    # Test violation types
    violation_types = test_violation_types()
    if not violation_types:
        print("No violation types found!")
        return
    
    # Get first vehicle from database for testing
    print("\n=== Getting test vehicle ===")
    # We'll use vehicle ID 1 (ABC-1234) which should exist from seed data
    vehicle_id = 1
    print(f"Using vehicle ID: {vehicle_id} (ABC-1234)")
    
    # Create a violation as officer
    violation = test_create_violation(
        officer_token, 
        vehicle_id, 
        violation_types[0]['id']  # Use first violation type
    )
    
    if violation:
        # Test getting violation by ticket number
        test_get_violation_by_ticket(violation['ticket_number'])
        
        # List violations as different roles
        test_list_violations(officer_token, "Officer")
        test_list_violations(admin_token, "Admin")
        test_list_violations(cashier_token, "Cashier")
        
        # Process payment as cashier
        payment = test_process_payment(
            cashier_token,
            violation['id'],
            violation['fine_amount']
        )
        
        # Check dashboard statistics for each role
        test_dashboard_stats(admin_token, "Admin")
        test_dashboard_stats(officer_token, "Officer")
        test_dashboard_stats(cashier_token, "Cashier")
    
    print("\n" + "=" * 60)
    print("Violation and Payment tests completed!")
    print("=" * 60)

if __name__ == "__main__":
    main()