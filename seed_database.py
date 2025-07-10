from database import SessionLocal, Owner, Vehicle
from datetime import date, datetime
import random

def seed_database():
    db = SessionLocal()
    
    # Check if data already exists
    if db.query(Owner).count() > 0:
        print("Database already has data. Skipping seed.")
        return
    
    print("Seeding database with sample data...")
    
    # Sample owners data
    owners_data = [
        {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@email.com",
            "phone": "+1234567890",
            "address": "123 Main Street",
            "city": "New York",
            "state": "NY",
            "zip_code": "10001"
        },
        {
            "first_name": "Jane",
            "last_name": "Smith",
            "email": "jane.smith@email.com",
            "phone": "+1234567891",
            "address": "456 Oak Avenue",
            "city": "Los Angeles",
            "state": "CA",
            "zip_code": "90001"
        },
        {
            "first_name": "Robert",
            "last_name": "Johnson",
            "email": "robert.j@email.com",
            "phone": "+1234567892",
            "address": "789 Pine Road",
            "city": "Chicago",
            "state": "IL",
            "zip_code": "60601"
        },
        {
            "first_name": "Maria",
            "last_name": "Garcia",
            "email": "maria.garcia@email.com",
            "phone": "+1234567893",
            "address": "321 Elm Street",
            "city": "Houston",
            "state": "TX",
            "zip_code": "77001"
        },
        {
            "first_name": "David",
            "last_name": "Brown",
            "email": "david.brown@email.com",
            "phone": "+1234567894",
            "address": "654 Maple Drive",
            "city": "Phoenix",
            "state": "AZ",
            "zip_code": "85001"
        }
    ]
    
    # Create owners
    owners = []
    for owner_data in owners_data:
        owner = Owner(**owner_data)
        db.add(owner)
        owners.append(owner)
    
    db.commit()
    
    # Sample vehicles data
    vehicles_data = [
        # John Doe's vehicles
        {
            "owner": owners[0],
            "plate_number": "ABC-1234",
            "make": "Toyota",
            "model": "Camry",
            "year": 2020,
            "color": "Silver",
            "vin": "1HGBH41JXMN109186",
            "registration_date": date(2020, 3, 15),
            "expiry_date": date(2025, 3, 15),
            "status": "active"
        },
        {
            "owner": owners[0],
            "plate_number": "XYZ-9876",
            "make": "Honda",
            "model": "Civic",
            "year": 2018,
            "color": "Blue",
            "vin": "2HGBH41JXMN109187",
            "registration_date": date(2018, 6, 20),
            "expiry_date": date(2024, 6, 20),
            "status": "expired"
        },
        # Jane Smith's vehicle
        {
            "owner": owners[1],
            "plate_number": "DEF-5678",
            "make": "Ford",
            "model": "Mustang",
            "year": 2022,
            "color": "Red",
            "vin": "3HGBH41JXMN109188",
            "registration_date": date(2022, 1, 10),
            "expiry_date": date(2026, 1, 10),
            "status": "active"
        },
        # Robert Johnson's vehicles
        {
            "owner": owners[2],
            "plate_number": "GHI-2468",
            "make": "Chevrolet",
            "model": "Silverado",
            "year": 2019,
            "color": "Black",
            "vin": "4HGBH41JXMN109189",
            "registration_date": date(2019, 9, 5),
            "expiry_date": date(2024, 9, 5),
            "status": "active"
        },
        {
            "owner": owners[2],
            "plate_number": "JKL-1357",
            "make": "Tesla",
            "model": "Model 3",
            "year": 2021,
            "color": "White",
            "vin": "5HGBH41JXMN109190",
            "registration_date": date(2021, 4, 12),
            "expiry_date": date(2025, 4, 12),
            "status": "active"
        },
        # Maria Garcia's vehicle
        {
            "owner": owners[3],
            "plate_number": "MNO-3579",
            "make": "Nissan",
            "model": "Altima",
            "year": 2020,
            "color": "Gray",
            "vin": "6HGBH41JXMN109191",
            "registration_date": date(2020, 7, 8),
            "expiry_date": date(2024, 7, 8),
            "status": "suspended"
        },
        # David Brown's vehicles
        {
            "owner": owners[4],
            "plate_number": "PQR-8642",
            "make": "BMW",
            "model": "X5",
            "year": 2023,
            "color": "Navy Blue",
            "vin": "7HGBH41JXMN109192",
            "registration_date": date(2023, 2, 28),
            "expiry_date": date(2027, 2, 28),
            "status": "active"
        },
        {
            "owner": owners[4],
            "plate_number": "STU-7531",
            "make": "Mercedes-Benz",
            "model": "C-Class",
            "year": 2022,
            "color": "Pearl White",
            "vin": "8HGBH41JXMN109193",
            "registration_date": date(2022, 11, 15),
            "expiry_date": date(2026, 11, 15),
            "status": "active"
        },
        # Additional common test plates
        {
            "owner": owners[0],
            "plate_number": "TEST123",
            "make": "Toyota",
            "model": "Corolla",
            "year": 2019,
            "color": "Green",
            "vin": "9HGBH41JXMN109194",
            "registration_date": date(2019, 5, 1),
            "expiry_date": date(2024, 5, 1),
            "status": "active"
        },
        {
            "owner": owners[1],
            "plate_number": "DEMO456",
            "make": "Hyundai",
            "model": "Elantra",
            "year": 2021,
            "color": "Silver",
            "vin": "0HGBH41JXMN109195",
            "registration_date": date(2021, 8, 20),
            "expiry_date": date(2025, 8, 20),
            "status": "active"
        }
    ]
    
    # Create vehicles
    for vehicle_data in vehicles_data:
        owner = vehicle_data.pop("owner")
        vehicle = Vehicle(owner_id=owner.id, **vehicle_data)
        db.add(vehicle)
    
    db.commit()
    
    print(f"Database seeded successfully!")
    print(f"Created {len(owners)} owners and {len(vehicles_data)} vehicles")
    print("\nSample plate numbers to test:")
    print("- ABC-1234 (John Doe - Active)")
    print("- XYZ-9876 (John Doe - Expired)")
    print("- DEF-5678 (Jane Smith - Active)")
    print("- MNO-3579 (Maria Garcia - Suspended)")
    print("- TEST123 (Test plate)")
    
    db.close()

if __name__ == "__main__":
    seed_database()