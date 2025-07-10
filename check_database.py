from database import SessionLocal, Owner, Vehicle
from sqlalchemy import text

db = SessionLocal()

print("Checking database contents...")

# Check owners
owner_count = db.query(Owner).count()
print(f"\nOwners in database: {owner_count}")

if owner_count > 0:
    print("Sample owners:")
    for owner in db.query(Owner).limit(3).all():
        print(f"  - {owner.first_name} {owner.last_name} (ID: {owner.id})")

# Check vehicles
vehicle_count = db.query(Vehicle).count()
print(f"\nVehicles in database: {vehicle_count}")

if vehicle_count > 0:
    print("Sample vehicles:")
    for vehicle in db.query(Vehicle).limit(5).all():
        print(f"  - {vehicle.plate_number} ({vehicle.make} {vehicle.model}) - Owner ID: {vehicle.owner_id}")

# Check for specific test plate
test_vehicle = db.query(Vehicle).filter(Vehicle.plate_number == "TEST123").first()
if test_vehicle:
    print(f"\nTEST123 found: {test_vehicle.make} {test_vehicle.model} owned by {test_vehicle.owner.first_name} {test_vehicle.owner.last_name}")
else:
    print("\nTEST123 NOT FOUND in database!")

# Raw query to see all plates
print("\nAll plate numbers in database:")
results = db.execute(text("SELECT plate_number FROM vehicles")).fetchall()
for row in results:
    print(f"  - {row[0]}")

db.close()