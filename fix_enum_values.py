#!/usr/bin/env python3
"""
Fix enum values in the database to match SQLAlchemy enum definitions
"""

from database import SessionLocal, engine
from sqlalchemy import text

def fix_enum_values():
    """Update database enum values to match SQLAlchemy definitions"""
    db = SessionLocal()
    
    try:
        # Fix violation status values
        print("Fixing violation status values...")
        db.execute(text("""
            UPDATE violations 
            SET status = 'PENDING' 
            WHERE status = 'pending'
        """))
        
        db.execute(text("""
            UPDATE violations 
            SET status = 'PAID' 
            WHERE status = 'paid'
        """))
        
        # Fix payment status values
        print("Fixing payment status values...")
        db.execute(text("""
            UPDATE payments 
            SET status = 'COMPLETED' 
            WHERE status = 'completed'
        """))
        
        # Fix payment method values
        print("Fixing payment method values...")
        db.execute(text("""
            UPDATE payments 
            SET payment_method = 'CASH' 
            WHERE payment_method = 'cash'
        """))
        
        db.commit()
        print("✓ Enum values fixed successfully!")
        
    except Exception as e:
        print(f"Error fixing enum values: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    fix_enum_values()