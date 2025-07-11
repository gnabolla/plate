from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import date, datetime
from enum import Enum

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

# Enums matching database enums
class UserRole(str, Enum):
    SUPER_ADMIN = "super_admin"
    OFFICER = "officer"
    CASHIER = "cashier"

class ViolationStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    APPEALED = "appealed"
    CANCELLED = "cancelled"
    OVERDUE = "overdue"

class PaymentStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"

class PaymentMethod(str, Enum):
    CASH = "cash"
    CREDIT_CARD = "credit_card"
    GCASH = "gcash"
    BANK_TRANSFER = "bank_transfer"
    ONLINE = "online"

class AppealStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    UNDER_REVIEW = "under_review"

# User schemas
class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    role: UserRole
    badge_number: Optional[str] = None
    department: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    badge_number: Optional[str] = None
    department: Optional[str] = None
    is_active: Optional[bool] = None

class User(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class UserInDB(User):
    hashed_password: str

# Violation Type schemas
class ViolationTypeBase(BaseModel):
    code: str
    name: str
    description: Optional[str] = None
    fine_amount: float = Field(gt=0)

class ViolationTypeCreate(ViolationTypeBase):
    pass

class ViolationTypeUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    fine_amount: Optional[float] = Field(None, gt=0)
    is_active: Optional[bool] = None

class ViolationType(ViolationTypeBase):
    id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

# Violation schemas
class ViolationBase(BaseModel):
    vehicle_id: Optional[int] = None
    violation_type_id: int
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    description: Optional[str] = None
    fine_amount: float = Field(gt=0)
    due_date: Optional[datetime] = None
    detection_log_id: Optional[int] = None

class ViolationCreate(ViolationBase):
    pass

class ViolationUpdate(BaseModel):
    status: Optional[ViolationStatus] = None
    description: Optional[str] = None
    due_date: Optional[datetime] = None

class Violation(ViolationBase):
    id: int
    ticket_number: str
    officer_id: int
    status: ViolationStatus
    issued_at: datetime
    officer: User
    violation_type: ViolationType
    vehicle: Optional[Vehicle] = None
    
    class Config:
        from_attributes = True

# Payment schemas
class PaymentBase(BaseModel):
    violation_id: int
    amount: float = Field(gt=0)
    payment_method: PaymentMethod
    reference_number: Optional[str] = None

class PaymentCreate(PaymentBase):
    pass

class Payment(PaymentBase):
    id: int
    transaction_id: str
    status: PaymentStatus
    cashier_id: Optional[int] = None
    payment_date: datetime
    receipt_number: Optional[str] = None
    cashier: Optional[User] = None
    violation: Violation
    
    class Config:
        from_attributes = True

# Appeal schemas
class AppealBase(BaseModel):
    violation_id: int
    reason: str
    evidence_path: Optional[str] = None

class AppealCreate(AppealBase):
    pass

class AppealUpdate(BaseModel):
    status: AppealStatus
    review_notes: Optional[str] = None

class Appeal(AppealBase):
    id: int
    status: AppealStatus
    submitted_at: datetime
    reviewed_at: Optional[datetime] = None
    reviewer_id: Optional[int] = None
    review_notes: Optional[str] = None
    reviewer: Optional[User] = None
    violation: Violation
    
    class Config:
        from_attributes = True

# Audit Log schemas
class AuditLogBase(BaseModel):
    action: str
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    old_values: Optional[str] = None
    new_values: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

class AuditLog(AuditLogBase):
    id: int
    user_id: Optional[int] = None
    created_at: datetime
    user: Optional[User] = None
    
    class Config:
        from_attributes = True

# Token schemas for authentication
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    username: Optional[str] = None

# Login schema
class UserLogin(BaseModel):
    username: str
    password: str