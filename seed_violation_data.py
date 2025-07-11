#!/usr/bin/env python3
"""
Seed violation types and create default super admin user
"""

from database import SessionLocal, engine, Base, User, ViolationType, UserRole
from passlib.context import CryptContext
from datetime import datetime
import sys

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def seed_violation_types(db):
    """Seed default violation types"""
    violation_types = [
        {
            "code": "V01",
            "name": "Overspeeding",
            "description": "Exceeding the posted speed limit",
            "fine_amount": 500.00
        },
        {
            "code": "V02",
            "name": "No License",
            "description": "Driving without a valid driver's license",
            "fine_amount": 1000.00
        },
        {
            "code": "V03",
            "name": "Reckless Driving",
            "description": "Operating a vehicle in a dangerous manner",
            "fine_amount": 1500.00
        },
        {
            "code": "V04",
            "name": "No Registration",
            "description": "Vehicle not properly registered",
            "fine_amount": 750.00
        },
        {
            "code": "V05",
            "name": "Illegal Parking",
            "description": "Parking in a prohibited area",
            "fine_amount": 300.00
        },
        {
            "code": "V06",
            "name": "No Helmet",
            "description": "Motorcycle rider not wearing helmet",
            "fine_amount": 500.00
        },
        {
            "code": "V07",
            "name": "Running Red Light",
            "description": "Failing to stop at a red traffic signal",
            "fine_amount": 1000.00
        },
        {
            "code": "V08",
            "name": "No Seatbelt",
            "description": "Driver or passenger not wearing seatbelt",
            "fine_amount": 750.00
        },
        {
            "code": "V09",
            "name": "Invalid Plates",
            "description": "Using expired or invalid license plates",
            "fine_amount": 5000.00
        },
        {
            "code": "V10",
            "name": "Overloading",
            "description": "Vehicle carrying passengers or cargo beyond capacity",
            "fine_amount": 1000.00
        }
    ]
    
    for vt_data in violation_types:
        # Check if violation type already exists
        existing = db.query(ViolationType).filter_by(code=vt_data["code"]).first()
        if not existing:
            violation_type = ViolationType(**vt_data)
            db.add(violation_type)
            print(f"Added violation type: {vt_data['code']} - {vt_data['name']}")
        else:
            print(f"Violation type already exists: {vt_data['code']} - {vt_data['name']}")
    
    db.commit()

def create_default_users(db):
    """Create default users for testing"""
    users = [
        {
            "username": "admin",
            "email": "admin@trafficviolations.ph",
            "full_name": "System Administrator",
            "role": UserRole.SUPER_ADMIN,
            "password": "admin123"  # Change this in production!
        },
        {
            "username": "officer1",
            "email": "officer1@trafficviolations.ph",
            "full_name": "Juan Dela Cruz",
            "role": UserRole.OFFICER,
            "badge_number": "TRF-001",
            "department": "Traffic Management Group",
            "password": "officer123"
        },
        {
            "username": "cashier1",
            "email": "cashier1@trafficviolations.ph",
            "full_name": "Maria Santos",
            "role": UserRole.CASHIER,
            "department": "Finance Department",
            "password": "cashier123"
        }
    ]
    
    for user_data in users:
        # Check if user already exists
        existing = db.query(User).filter_by(username=user_data["username"]).first()
        if not existing:
            password = user_data.pop("password")
            user = User(
                **user_data,
                hashed_password=hash_password(password)
            )
            db.add(user)
            print(f"Created user: {user_data['username']} ({user_data['role'].value})")
        else:
            print(f"User already exists: {user_data['username']}")
    
    db.commit()

def main():
    """Main seeding function"""
    print("Starting database seeding...")
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Get database session
    db = SessionLocal()
    
    try:
        # Seed violation types
        print("\nSeeding violation types...")
        seed_violation_types(db)
        
        # Create default users
        print("\nCreating default users...")
        create_default_users(db)
        
        print("\nDatabase seeding completed successfully!")
        print("\nDefault users created:")
        print("  - Super Admin: username='admin', password='admin123'")
        print("  - Officer: username='officer1', password='officer123'")
        print("  - Cashier: username='cashier1', password='cashier123'")
        print("\n⚠️  Remember to change these passwords in production!")
        
    except Exception as e:
        print(f"Error seeding database: {e}")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    main()