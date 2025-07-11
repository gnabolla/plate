#!/usr/bin/env python3
"""
Clean up violations with incorrect enum values
"""

from database import SessionLocal, engine
from sqlalchemy import text

def cleanup_violations():
    """Delete violations with incorrect enum values"""
    db = SessionLocal()
    
    try:
        # Delete violations with lowercase status values
        print("Cleaning up violations with incorrect status values...")
        result = db.execute(text("""
            DELETE FROM violations 
            WHERE status IN ('pending', 'paid', 'appealed', 'cancelled', 'overdue')
        """))
        
        db.commit()
        print(f"✓ Deleted {result.rowcount} violations with incorrect status values")
        
    except Exception as e:
        print(f"Error cleaning up violations: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    cleanup_violations()