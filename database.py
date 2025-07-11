from sqlalchemy import create_engine, Column, Integer, String, DateTime, Date, ForeignKey, Text, Boolean, Float, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os
import enum

# Create database directory if it doesn't exist
os.makedirs("data", exist_ok=True)

# Database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./data/plate_detection.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Models
class Owner(Base):
    __tablename__ = "owners"
    
    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255))
    phone = Column(String(20))
    address = Column(Text)
    city = Column(String(100))
    state = Column(String(50))
    zip_code = Column(String(10))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    vehicles = relationship("Vehicle", back_populates="owner")

class Vehicle(Base):
    __tablename__ = "vehicles"
    
    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("owners.id"), nullable=False)
    plate_number = Column(String(20), unique=True, nullable=False, index=True)
    make = Column(String(50))
    model = Column(String(50))
    year = Column(Integer)
    color = Column(String(30))
    vin = Column(String(17))
    registration_date = Column(Date)
    expiry_date = Column(Date)
    status = Column(String(20), default="active")  # active, expired, suspended
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    owner = relationship("Owner", back_populates="vehicles")
    detections = relationship("DetectionLog", back_populates="vehicle")

class DetectionLog(Base):
    __tablename__ = "detection_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    plate_number = Column(String(20))
    detected_text = Column(String(20))
    confidence = Column(Integer)
    source = Column(String(20))  # upload, camera, manual
    image_path = Column(String(255))
    detected_at = Column(DateTime, default=datetime.utcnow)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"))
    
    # Relationship
    vehicle = relationship("Vehicle", back_populates="detections")

# Enums for user roles and status
class UserRole(enum.Enum):
    SUPER_ADMIN = "super_admin"
    OFFICER = "officer"
    CASHIER = "cashier"

class ViolationStatus(enum.Enum):
    PENDING = "pending"
    PAID = "paid"
    APPEALED = "appealed"
    CANCELLED = "cancelled"
    OVERDUE = "overdue"

class PaymentStatus(enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"

class PaymentMethod(enum.Enum):
    CASH = "cash"
    CREDIT_CARD = "credit_card"
    GCASH = "gcash"
    BANK_TRANSFER = "bank_transfer"
    ONLINE = "online"

class AppealStatus(enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    UNDER_REVIEW = "under_review"

# User model for authentication
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100))
    role = Column(Enum(UserRole), nullable=False)
    is_active = Column(Boolean, default=True)
    badge_number = Column(String(50))  # For officers
    department = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    violations_issued = relationship("Violation", back_populates="officer", foreign_keys="Violation.officer_id")
    payments_processed = relationship("Payment", back_populates="cashier")
    audit_logs = relationship("AuditLog", back_populates="user")

# Violation Types
class ViolationType(Base):
    __tablename__ = "violation_types"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(10), unique=True, nullable=False)  # V01, V02, etc.
    name = Column(String(100), nullable=False)
    description = Column(Text)
    fine_amount = Column(Float, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    violations = relationship("Violation", back_populates="violation_type")

# Violations
class Violation(Base):
    __tablename__ = "violations"
    
    id = Column(Integer, primary_key=True, index=True)
    ticket_number = Column(String(20), unique=True, nullable=False, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"))
    violation_type_id = Column(Integer, ForeignKey("violation_types.id"), nullable=False)
    officer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    location = Column(String(255))
    latitude = Column(Float)
    longitude = Column(Float)
    description = Column(Text)
    fine_amount = Column(Float, nullable=False)
    status = Column(Enum(ViolationStatus), default=ViolationStatus.PENDING)
    issued_at = Column(DateTime, default=datetime.utcnow)
    due_date = Column(DateTime)
    detection_log_id = Column(Integer, ForeignKey("detection_logs.id"))  # Link to plate detection
    
    # Relationships
    vehicle = relationship("Vehicle", backref="violations")
    violation_type = relationship("ViolationType", back_populates="violations")
    officer = relationship("User", back_populates="violations_issued", foreign_keys=[officer_id])
    payments = relationship("Payment", back_populates="violation")
    appeals = relationship("Appeal", back_populates="violation")
    detection_log = relationship("DetectionLog", backref="violation")

# Payments
class Payment(Base):
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(String(50), unique=True, nullable=False)
    violation_id = Column(Integer, ForeignKey("violations.id"), nullable=False)
    amount = Column(Float, nullable=False)
    payment_method = Column(Enum(PaymentMethod), nullable=False)
    status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    cashier_id = Column(Integer, ForeignKey("users.id"))
    payment_date = Column(DateTime, default=datetime.utcnow)
    reference_number = Column(String(100))  # For online payments
    receipt_number = Column(String(50))
    
    # Relationships
    violation = relationship("Violation", back_populates="payments")
    cashier = relationship("User", back_populates="payments_processed")

# Appeals
class Appeal(Base):
    __tablename__ = "appeals"
    
    id = Column(Integer, primary_key=True, index=True)
    violation_id = Column(Integer, ForeignKey("violations.id"), nullable=False)
    reason = Column(Text, nullable=False)
    evidence_path = Column(String(255))  # Path to uploaded evidence
    status = Column(Enum(AppealStatus), default=AppealStatus.PENDING)
    submitted_at = Column(DateTime, default=datetime.utcnow)
    reviewed_at = Column(DateTime)
    reviewer_id = Column(Integer, ForeignKey("users.id"))
    review_notes = Column(Text)
    
    # Relationships
    violation = relationship("Violation", back_populates="appeals")
    reviewer = relationship("User", backref="appeals_reviewed")

# Audit Log
class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    action = Column(String(100), nullable=False)
    entity_type = Column(String(50))  # violation, payment, user, etc.
    entity_id = Column(Integer)
    old_values = Column(Text)  # JSON string
    new_values = Column(Text)  # JSON string
    ip_address = Column(String(45))
    user_agent = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")

# Create tables
Base.metadata.create_all(bind=engine)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()