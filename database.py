from sqlalchemy import create_engine, Column, Integer, String, DateTime, Date, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

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

# Create tables
Base.metadata.create_all(bind=engine)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()