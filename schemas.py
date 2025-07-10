from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime

# Owner schemas
class OwnerBase(BaseModel):
    first_name: str
    last_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None

class OwnerCreate(OwnerBase):
    pass

class Owner(OwnerBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Vehicle schemas
class VehicleBase(BaseModel):
    plate_number: str
    make: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    color: Optional[str] = None
    vin: Optional[str] = None
    registration_date: Optional[date] = None
    expiry_date: Optional[date] = None
    status: Optional[str] = "active"

class VehicleCreate(VehicleBase):
    owner_id: int

class Vehicle(VehicleBase):
    id: int
    owner_id: int
    created_at: datetime
    owner: Owner
    
    class Config:
        from_attributes = True

# Detection schemas
class DetectionLogBase(BaseModel):
    plate_number: str
    detected_text: str
    confidence: int
    source: str
    image_path: Optional[str] = None

class DetectionLog(DetectionLogBase):
    id: int
    detected_at: datetime
    vehicle_id: Optional[int] = None
    vehicle: Optional[Vehicle] = None
    
    class Config:
        from_attributes = True

# Combined schemas for responses
class VehicleWithOwner(BaseModel):
    vehicle: Vehicle
    owner: Owner
    
    class Config:
        from_attributes = True