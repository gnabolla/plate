from fastapi import FastAPI, UploadFile, File, Form, Request, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import func
import pytesseract
import cv2
import numpy as np
import os
import re
from typing import Optional, List
import base64
from PIL import Image
import io
import imutils
from datetime import datetime, timedelta

# Import database models and schemas
from database import get_db, Owner, Vehicle, DetectionLog, User, ViolationType, Violation, Payment, Appeal, AuditLog, ViolationStatus, PaymentStatus, PaymentMethod, AppealStatus
import schemas
from auth import (
    authenticate_user, create_access_token, get_current_active_user,
    get_current_super_admin, get_current_officer, get_current_cashier,
    hash_password, create_audit_log, ACCESS_TOKEN_EXPIRE_MINUTES
)

app = FastAPI(
    title="Traffic Violation Management System",
    description="License plate detection with integrated violation management",
    version="1.0.0"
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

os.makedirs("uploads", exist_ok=True)

# ==================== Authentication Endpoints ====================

@app.post("/api/auth/login", response_model=schemas.Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
    request: Request = None
):
    """Login endpoint that returns JWT token"""
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        # Log failed login attempt
        create_audit_log(
            db, None, "LOGIN_FAILED",
            entity_type="user",
            ip_address=request.client.host if request else None,
            user_agent=request.headers.get("user-agent") if request else None
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    # Log successful login
    create_audit_log(
        db, user, "LOGIN_SUCCESS",
        entity_type="user",
        entity_id=user.id,
        ip_address=request.client.host if request else None,
        user_agent=request.headers.get("user-agent") if request else None
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/api/auth/logout")
async def logout(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    request: Request = None
):
    """Logout endpoint (mainly for audit logging)"""
    create_audit_log(
        db, current_user, "LOGOUT",
        entity_type="user",
        entity_id=current_user.id,
        ip_address=request.client.host if request else None,
        user_agent=request.headers.get("user-agent") if request else None
    )
    return {"message": "Successfully logged out"}

@app.get("/api/auth/me", response_model=schemas.User)
async def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """Get current user information"""
    return current_user

# ==================== User Management Endpoints (Super Admin Only) ====================

@app.post("/api/users", response_model=schemas.User)
async def create_user(
    user_data: schemas.UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_super_admin)
):
    """Create a new user (Super Admin only)"""
    # Check if username already exists
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email already exists
    existing_email = db.query(User).filter(User.email == user_data.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    user_dict = user_data.dict()
    password = user_dict.pop("password")
    new_user = User(
        **user_dict,
        hashed_password=hash_password(password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Log user creation
    create_audit_log(
        db, current_user, "USER_CREATED",
        entity_type="user",
        entity_id=new_user.id,
        new_values={"username": new_user.username, "role": new_user.role.value}
    )
    
    return new_user

@app.get("/api/users", response_model=List[schemas.User])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_super_admin)
):
    """List all users (Super Admin only)"""
    users = db.query(User).offset(skip).limit(limit).all()
    return users

@app.put("/api/users/{user_id}", response_model=schemas.User)
async def update_user(
    user_id: int,
    user_update: schemas.UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_super_admin)
):
    """Update user information (Super Admin only)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Store old values for audit
    old_values = {
        "email": user.email,
        "full_name": user.full_name,
        "is_active": user.is_active
    }
    
    # Update user fields
    update_data = user_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    
    user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user)
    
    # Log user update
    create_audit_log(
        db, current_user, "USER_UPDATED",
        entity_type="user",
        entity_id=user.id,
        old_values=old_values,
        new_values=update_data
    )
    
    return user

@app.delete("/api/users/{user_id}")
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_super_admin)
):
    """Delete (deactivate) a user (Super Admin only)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Don't allow deleting self
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    # Soft delete by deactivating
    user.is_active = False
    user.updated_at = datetime.utcnow()
    db.commit()
    
    # Log user deletion
    create_audit_log(
        db, current_user, "USER_DEACTIVATED",
        entity_type="user",
        entity_id=user.id
    )
    
    return {"message": "User deactivated successfully"}

# ==================== Violation Type Management (Super Admin Only) ====================

@app.get("/api/violation-types", response_model=List[schemas.ViolationType])
async def list_violation_types(
    skip: int = 0,
    limit: int = 100,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """List all violation types (public endpoint for officers to see available types)"""
    query = db.query(ViolationType)
    if is_active is not None:
        query = query.filter(ViolationType.is_active == is_active)
    violation_types = query.offset(skip).limit(limit).all()
    return violation_types

@app.post("/api/violation-types", response_model=schemas.ViolationType)
async def create_violation_type(
    violation_type: schemas.ViolationTypeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_super_admin)
):
    """Create a new violation type (Super Admin only)"""
    # Check if code already exists
    existing = db.query(ViolationType).filter(ViolationType.code == violation_type.code).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Violation type code already exists"
        )
    
    new_violation_type = ViolationType(**violation_type.dict())
    db.add(new_violation_type)
    db.commit()
    db.refresh(new_violation_type)
    
    # Log creation
    create_audit_log(
        db, current_user, "VIOLATION_TYPE_CREATED",
        entity_type="violation_type",
        entity_id=new_violation_type.id,
        new_values=violation_type.dict()
    )
    
    return new_violation_type

@app.put("/api/violation-types/{type_id}", response_model=schemas.ViolationType)
async def update_violation_type(
    type_id: int,
    violation_update: schemas.ViolationTypeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_super_admin)
):
    """Update violation type (Super Admin only)"""
    violation_type = db.query(ViolationType).filter(ViolationType.id == type_id).first()
    if not violation_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Violation type not found"
        )
    
    # Store old values for audit
    old_values = {
        "name": violation_type.name,
        "fine_amount": violation_type.fine_amount,
        "is_active": violation_type.is_active
    }
    
    # Update fields
    update_data = violation_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(violation_type, field, value)
    
    db.commit()
    db.refresh(violation_type)
    
    # Log update
    create_audit_log(
        db, current_user, "VIOLATION_TYPE_UPDATED",
        entity_type="violation_type",
        entity_id=violation_type.id,
        old_values=old_values,
        new_values=update_data
    )
    
    return violation_type

# ==================== Violation Management ====================

@app.post("/api/violations", response_model=schemas.Violation)
async def create_violation(
    violation_data: schemas.ViolationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_officer),
    request: Request = None
):
    """Create a new violation (Officers and Super Admins only)"""
    # Verify vehicle exists if provided
    if violation_data.vehicle_id:
        vehicle = db.query(Vehicle).filter(Vehicle.id == violation_data.vehicle_id).first()
        if not vehicle:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vehicle not found"
            )
    
    # Verify violation type exists
    violation_type = db.query(ViolationType).filter(
        ViolationType.id == violation_data.violation_type_id
    ).first()
    if not violation_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Violation type not found"
        )
    
    # Generate unique ticket number
    import random
    import string
    ticket_number = f"TKT-{datetime.now().strftime('%Y%m%d')}-{''.join(random.choices(string.ascii_uppercase + string.digits, k=6))}"
    
    # Create violation
    violation_dict = violation_data.dict()
    new_violation = Violation(
        **violation_dict,
        ticket_number=ticket_number,
        officer_id=current_user.id,
        issued_at=datetime.utcnow(),
        status=ViolationStatus.PENDING  # Use database enum
    )
    
    # Set due date if not provided (default: 30 days from now)
    if not new_violation.due_date:
        new_violation.due_date = datetime.utcnow() + timedelta(days=30)
    
    db.add(new_violation)
    db.commit()
    db.refresh(new_violation)
    
    # Log violation creation
    create_audit_log(
        db, current_user, "VIOLATION_CREATED",
        entity_type="violation",
        entity_id=new_violation.id,
        new_values={
            "ticket_number": new_violation.ticket_number,
            "vehicle_id": new_violation.vehicle_id,
            "violation_type_id": new_violation.violation_type_id,
            "fine_amount": new_violation.fine_amount
        },
        ip_address=request.client.host if request else None
    )
    
    return new_violation

@app.get("/api/violations", response_model=List[schemas.Violation])
async def list_violations(
    skip: int = 0,
    limit: int = 100,
    status: Optional[schemas.ViolationStatus] = None,
    vehicle_id: Optional[int] = None,
    officer_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """List violations with filters"""
    query = db.query(Violation)
    
    # Apply filters based on user role
    if current_user.role == schemas.UserRole.OFFICER:
        # Officers can only see their own violations
        query = query.filter(Violation.officer_id == current_user.id)
    elif current_user.role == schemas.UserRole.CASHIER:
        # Cashiers can see all violations but mainly interested in pending payments
        if not status:
            status = ViolationStatus.PENDING
    
    # Apply additional filters
    if status:
        query = query.filter(Violation.status == status)
    if vehicle_id:
        query = query.filter(Violation.vehicle_id == vehicle_id)
    if officer_id and current_user.role == schemas.UserRole.SUPER_ADMIN:
        query = query.filter(Violation.officer_id == officer_id)
    
    violations = query.order_by(Violation.issued_at.desc()).offset(skip).limit(limit).all()
    return violations

@app.get("/api/violations/{violation_id}", response_model=schemas.Violation)
async def get_violation(
    violation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get specific violation details"""
    violation = db.query(Violation).filter(Violation.id == violation_id).first()
    if not violation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Violation not found"
        )
    
    # Check permissions
    if current_user.role == schemas.UserRole.OFFICER and violation.officer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view violations you issued"
        )
    
    return violation

@app.get("/api/violations/ticket/{ticket_number}", response_model=schemas.Violation)
async def get_violation_by_ticket(
    ticket_number: str,
    db: Session = Depends(get_db)
):
    """Get violation by ticket number (public endpoint for payment lookup)"""
    violation = db.query(Violation).filter(Violation.ticket_number == ticket_number).first()
    if not violation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Violation not found with this ticket number"
        )
    
    return violation

@app.put("/api/violations/{violation_id}", response_model=schemas.Violation)
async def update_violation(
    violation_id: int,
    violation_update: schemas.ViolationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update violation (status changes, etc.)"""
    violation = db.query(Violation).filter(Violation.id == violation_id).first()
    if not violation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Violation not found"
        )
    
    # Check permissions
    if current_user.role == schemas.UserRole.OFFICER and violation.officer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update violations you issued"
        )
    
    # Store old values for audit
    old_values = {
        "status": violation.status.value if violation.status else None,
        "description": violation.description,
        "due_date": violation.due_date.isoformat() if violation.due_date else None
    }
    
    # Update fields
    update_data = violation_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(violation, field, value)
    
    db.commit()
    db.refresh(violation)
    
    # Log update
    create_audit_log(
        db, current_user, "VIOLATION_UPDATED",
        entity_type="violation",
        entity_id=violation.id,
        old_values=old_values,
        new_values=update_data
    )
    
    return violation

# ==================== Appeal Management ====================

@app.post("/api/appeals", response_model=schemas.Appeal)
async def create_appeal(
    appeal_data: schemas.AppealCreate,
    db: Session = Depends(get_db)
):
    """Create an appeal for a violation (public endpoint)"""
    # Verify violation exists
    violation = db.query(Violation).filter(Violation.id == appeal_data.violation_id).first()
    if not violation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Violation not found"
        )
    
    # Check if appeal already exists
    existing_appeal = db.query(Appeal).filter(
        Appeal.violation_id == appeal_data.violation_id,
        Appeal.status.in_([AppealStatus.PENDING, AppealStatus.UNDER_REVIEW])
    ).first()
    if existing_appeal:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An appeal is already pending for this violation"
        )
    
    # Create appeal
    new_appeal = Appeal(**appeal_data.dict())
    db.add(new_appeal)
    
    # Update violation status
    violation.status = ViolationStatus.APPEALED
    
    db.commit()
    db.refresh(new_appeal)
    
    return new_appeal

@app.get("/api/appeals", response_model=List[schemas.Appeal])
async def list_appeals(
    skip: int = 0,
    limit: int = 100,
    status: Optional[schemas.AppealStatus] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_super_admin)
):
    """List all appeals (Super Admin only)"""
    query = db.query(Appeal)
    if status:
        query = query.filter(Appeal.status == status)
    
    appeals = query.order_by(Appeal.submitted_at.desc()).offset(skip).limit(limit).all()
    return appeals

@app.put("/api/appeals/{appeal_id}", response_model=schemas.Appeal)
async def update_appeal(
    appeal_id: int,
    appeal_update: schemas.AppealUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_super_admin)
):
    """Update appeal status (Super Admin only)"""
    appeal = db.query(Appeal).filter(Appeal.id == appeal_id).first()
    if not appeal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appeal not found"
        )
    
    # Update appeal
    appeal.status = appeal_update.status
    appeal.review_notes = appeal_update.review_notes
    appeal.reviewer_id = current_user.id
    appeal.reviewed_at = datetime.utcnow()
    
    # Update violation status based on appeal outcome
    violation = appeal.violation
    if appeal_update.status == AppealStatus.APPROVED:
        violation.status = ViolationStatus.CANCELLED
    elif appeal_update.status == AppealStatus.REJECTED:
        violation.status = ViolationStatus.PENDING
    
    db.commit()
    db.refresh(appeal)
    
    # Log appeal update
    create_audit_log(
        db, current_user, "APPEAL_REVIEWED",
        entity_type="appeal",
        entity_id=appeal.id,
        new_values={
            "status": appeal_update.status.value,
            "review_notes": appeal_update.review_notes
        }
    )
    
    return appeal

# ==================== Payment Processing ====================

@app.post("/api/payments", response_model=schemas.Payment)
async def process_payment(
    payment_data: schemas.PaymentCreate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_cashier)
):
    """Process a payment for a violation (Cashiers and Super Admins)"""
    # Verify violation exists
    violation = db.query(Violation).filter(Violation.id == payment_data.violation_id).first()
    if not violation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Violation not found"
        )
    
    # Check if violation is already paid
    if violation.status == ViolationStatus.PAID:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This violation has already been paid"
        )
    
    # Generate transaction ID
    import uuid
    transaction_id = f"PAY-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
    
    # Generate receipt number
    receipt_number = f"RCP-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # Create payment record
    payment = Payment(
        transaction_id=transaction_id,
        receipt_number=receipt_number,
        violation_id=payment_data.violation_id,
        amount=payment_data.amount,
        payment_method=PaymentMethod[payment_data.payment_method.upper()],  # Use database enum
        reference_number=payment_data.reference_number,
        status=PaymentStatus.COMPLETED,
        cashier_id=current_user.id if current_user else None,
        payment_date=datetime.utcnow()
    )
    
    # Update violation status
    violation.status = ViolationStatus.PAID
    
    db.add(payment)
    db.commit()
    db.refresh(payment)
    
    # Log payment
    create_audit_log(
        db, current_user, "PAYMENT_PROCESSED",
        entity_type="payment",
        entity_id=payment.id,
        new_values={
            "transaction_id": payment.transaction_id,
            "amount": payment.amount,
            "payment_method": payment.payment_method.value,
            "violation_id": payment.violation_id
        }
    )
    
    return payment

@app.get("/api/payments", response_model=List[schemas.Payment])
async def list_payments(
    skip: int = 0,
    limit: int = 100,
    status: Optional[schemas.PaymentStatus] = None,
    payment_method: Optional[schemas.PaymentMethod] = None,
    cashier_id: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """List payments with filters"""
    query = db.query(Payment)
    
    # Role-based filtering
    if current_user.role == schemas.UserRole.CASHIER:
        # Cashiers can only see their own processed payments
        query = query.filter(Payment.cashier_id == current_user.id)
    
    # Apply filters
    if status:
        query = query.filter(Payment.status == status)
    if payment_method:
        query = query.filter(Payment.payment_method == payment_method)
    if cashier_id and current_user.role == schemas.UserRole.SUPER_ADMIN:
        query = query.filter(Payment.cashier_id == cashier_id)
    if start_date:
        query = query.filter(Payment.payment_date >= start_date)
    if end_date:
        query = query.filter(Payment.payment_date <= end_date)
    
    payments = query.order_by(Payment.payment_date.desc()).offset(skip).limit(limit).all()
    return payments

@app.get("/api/payments/{payment_id}", response_model=schemas.Payment)
async def get_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get specific payment details"""
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )
    
    # Check permissions
    if current_user.role == schemas.UserRole.CASHIER and payment.cashier_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view payments you processed"
        )
    
    return payment

@app.get("/api/violations/{violation_id}/payments", response_model=List[schemas.Payment])
async def get_violation_payments(
    violation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all payments for a specific violation"""
    violation = db.query(Violation).filter(Violation.id == violation_id).first()
    if not violation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Violation not found"
        )
    
    payments = db.query(Payment).filter(Payment.violation_id == violation_id).all()
    return payments

# ==================== Dashboard/Statistics Endpoints ====================

@app.get("/api/dashboard/statistics")
async def get_dashboard_statistics(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get dashboard statistics based on user role"""
    stats = {}
    
    if current_user.role == schemas.UserRole.SUPER_ADMIN:
        # Admin sees everything
        stats["total_violations"] = db.query(Violation).count()
        stats["pending_violations"] = db.query(Violation).filter(
            Violation.status == ViolationStatus.PENDING
        ).count()
        stats["paid_violations"] = db.query(Violation).filter(
            Violation.status == ViolationStatus.PAID
        ).count()
        stats["total_revenue"] = db.query(Payment).filter(
            Payment.status == PaymentStatus.COMPLETED
        ).with_entities(func.sum(Payment.amount)).scalar() or 0
        stats["active_officers"] = db.query(User).filter(
            User.role == schemas.UserRole.OFFICER,
            User.is_active == True
        ).count()
        stats["pending_appeals"] = db.query(Appeal).filter(
            Appeal.status == AppealStatus.PENDING
        ).count()
        
    elif current_user.role == schemas.UserRole.OFFICER:
        # Officers see their own statistics
        stats["my_violations_issued"] = db.query(Violation).filter(
            Violation.officer_id == current_user.id
        ).count()
        stats["my_violations_paid"] = db.query(Violation).filter(
            Violation.officer_id == current_user.id,
            Violation.status == ViolationStatus.PAID
        ).count()
        stats["my_violations_pending"] = db.query(Violation).filter(
            Violation.officer_id == current_user.id,
            Violation.status == ViolationStatus.PENDING
        ).count()
        
    elif current_user.role == schemas.UserRole.CASHIER:
        # Cashiers see payment statistics
        stats["payments_processed_today"] = db.query(Payment).filter(
            Payment.cashier_id == current_user.id,
            Payment.payment_date >= datetime.now().replace(hour=0, minute=0, second=0)
        ).count()
        stats["total_collected_today"] = db.query(Payment).filter(
            Payment.cashier_id == current_user.id,
            Payment.payment_date >= datetime.now().replace(hour=0, minute=0, second=0),
            Payment.status == PaymentStatus.COMPLETED
        ).with_entities(func.sum(Payment.amount)).scalar() or 0
        stats["pending_payments"] = db.query(Violation).filter(
            Violation.status == ViolationStatus.PENDING
        ).count()
    
    return stats

# ==================== Existing Routes ====================

def normalize_plate_number(plate):
    """Normalize plate number by removing spaces, hyphens, and converting to uppercase"""
    if not plate:
        return ""
    # Remove all non-alphanumeric characters and convert to uppercase
    normalized = re.sub(r'[^A-Za-z0-9]', '', plate).upper()
    return normalized

def preprocess_image(image):
    """Preprocess image for better OCR accuracy"""
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Simple preprocessing - just return grayscale for now
    # This will help us debug if the complex preprocessing is the issue
    return gray

def extract_plate_number(text):
    """Extract likely license plate patterns from OCR text"""
    # Clean the text
    text = text.upper().strip()
    
    # Remove common OCR artifacts
    text = text.replace('|', 'I')
    text = text.replace('0', 'O')
    text = text.replace('$', 'S')
    text = text.replace('&', '8')
    
    # Common license plate patterns
    patterns = [
        r'[A-Z]{2,3}[-\s]?\d{3,4}',  # AB-1234 or ABC-123
        r'\d{2,3}[-\s]?[A-Z]{2,3}[-\s]?\d{2,4}',  # 12-ABC-34
        r'[A-Z]{1,3}\d{1,4}[A-Z]{0,3}',  # A123B or ABC1234
        r'\d{1,4}[A-Z]{1,3}\d{0,4}',  # 1234ABC
        r'[A-Z0-9]{4,10}',  # General alphanumeric
    ]
    
    candidates = []
    
    for pattern in patterns:
        matches = re.findall(pattern, text)
        candidates.extend(matches)
    
    # Filter candidates by length (most plates are 5-8 characters)
    candidates = [c for c in candidates if 4 <= len(c.replace('-', '').replace(' ', '')) <= 10]
    
    # Add hyphenated versions for common patterns
    additional_candidates = []
    for c in candidates:
        # If it looks like ABC1234, also try ABC-1234
        if re.match(r'^[A-Z]{3}\d{4}$', c):
            additional_candidates.append(f"{c[:3]}-{c[3:]}")
        # If it looks like AB1234, also try AB-1234
        elif re.match(r'^[A-Z]{2}\d{4}$', c):
            additional_candidates.append(f"{c[:2]}-{c[2:]}")
    
    candidates.extend(additional_candidates)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_candidates = []
    for c in candidates:
        if c not in seen:
            seen.add(c)
            unique_candidates.append(c)
    
    return unique_candidates

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/admin", response_class=HTMLResponse)
async def admin(request: Request, db: Session = Depends(get_db)):
    owners = db.query(Owner).all()
    return templates.TemplateResponse("admin.html", {"request": request, "owners": owners})

# API Endpoints for database operations
@app.post("/api/owners", response_model=schemas.Owner)
async def create_owner(owner: schemas.OwnerCreate, db: Session = Depends(get_db)):
    db_owner = Owner(**owner.dict())
    db.add(db_owner)
    db.commit()
    db.refresh(db_owner)
    return db_owner

@app.get("/api/owners", response_model=List[schemas.Owner])
async def get_owners(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    owners = db.query(Owner).offset(skip).limit(limit).all()
    return owners

@app.post("/api/vehicles", response_model=schemas.Vehicle)
async def create_vehicle(vehicle: schemas.VehicleCreate, db: Session = Depends(get_db)):
    # Normalize the plate number to uppercase for consistent storage
    vehicle_data = vehicle.dict()
    vehicle_data['plate_number'] = vehicle_data['plate_number'].upper()
    
    # Check if plate already exists
    existing = db.query(Vehicle).filter(Vehicle.plate_number == vehicle_data['plate_number']).first()
    if existing:
        raise HTTPException(status_code=400, detail="Plate number already registered")
    
    db_vehicle = Vehicle(**vehicle_data)
    db.add(db_vehicle)
    db.commit()
    db.refresh(db_vehicle)
    return db_vehicle

@app.get("/api/vehicles/{plate_number}", response_model=schemas.Vehicle)
async def get_vehicle(plate_number: str, db: Session = Depends(get_db)):
    vehicle = db.query(Vehicle).filter(Vehicle.plate_number == plate_number.upper()).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return vehicle

@app.get("/api/detection-logs", response_model=List[schemas.DetectionLog])
async def get_detection_logs(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    logs = db.query(DetectionLog).order_by(DetectionLog.detected_at.desc()).offset(skip).limit(limit).all()
    return logs

@app.post("/detect")
async def detect_plate(
    file: Optional[UploadFile] = File(None),
    image_data: Optional[str] = Form(None),
    manual_plate: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    try:
        if manual_plate:
            # Check database for manual input too
            plate_upper = manual_plate.upper()
            normalized_input = normalize_plate_number(manual_plate)
            print(f"Searching for plate: {plate_upper} (normalized: {normalized_input})")  # Debug
            
            # Query database - try to find vehicles where normalized plate matches
            all_vehicles = db.query(Vehicle).all()
            vehicle = None
            print(f"Total vehicles in database: {len(all_vehicles)}")  # Debug
            for v in all_vehicles:
                normalized_db = normalize_plate_number(v.plate_number)
                print(f"DB plate: {v.plate_number} -> normalized: {normalized_db}")  # Debug
                if normalized_db == normalized_input:
                    vehicle = v
                    print(f"MATCH FOUND! Plate: {v.plate_number}, Owner: {v.owner.first_name} {v.owner.last_name}")  # Debug
                    break
            
            print(f"Vehicle found: {vehicle is not None}")  # Debug
            
            # Log the detection
            detection_log = DetectionLog(
                plate_number=plate_upper,
                detected_text=plate_upper,
                confidence=100,
                source="manual",
                vehicle_id=vehicle.id if vehicle else None
            )
            db.add(detection_log)
            db.commit()
            
            result = {
                "text": plate_upper,
                "confidence": 100
            }
            
            if vehicle:
                result['vehicle_info'] = {
                    "make": vehicle.make,
                    "model": vehicle.model,
                    "year": vehicle.year,
                    "color": vehicle.color,
                    "status": vehicle.status,
                    "owner": {
                        "name": f"{vehicle.owner.first_name} {vehicle.owner.last_name}",
                        "email": vehicle.owner.email,
                        "phone": vehicle.owner.phone,
                        "city": vehicle.owner.city,
                        "state": vehicle.owner.state
                    }
                }
            
            return JSONResponse({
                "success": True,
                "plates": [result],
                "source": "manual"
            })
        
        image = None
        
        if file:
            contents = await file.read()
            nparr = np.frombuffer(contents, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            source = "upload"
        elif image_data:
            image_data = image_data.split(',')[1]
            image_bytes = base64.b64decode(image_data)
            img = Image.open(io.BytesIO(image_bytes))
            image = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
            source = "camera"
        else:
            return JSONResponse({
                "success": False,
                "error": "No image or manual input provided"
            })
        
        if image is None:
            return JSONResponse({
                "success": False,
                "error": "Failed to process image"
            })
        
        # Preprocess the image
        processed_image = preprocess_image(image)
        
        # Run OCR with different configurations
        configs = [
            '--psm 8 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',
            '--psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',
            '--psm 13',
            '--psm 11',
        ]
        
        all_text = []
        for config in configs:
            try:
                text = pytesseract.image_to_string(processed_image, config=config)
                all_text.append(text)
            except Exception as e:
                pass
        
        # Combine all OCR results
        combined_text = ' '.join(all_text)
        
        # Extract plate numbers
        plate_candidates = extract_plate_number(combined_text)
        
        # Also try OCR on the original image
        try:
            text = pytesseract.image_to_string(image)
            more_candidates = extract_plate_number(text)
            plate_candidates.extend(more_candidates)
        except Exception as e:
            pass
        
        # Remove duplicates and create results
        seen = set()
        plates = []
        for plate in plate_candidates:
            clean_plate = plate.replace('-', '').replace(' ', '')
            if clean_plate not in seen and len(clean_plate) >= 4:
                seen.add(clean_plate)
                plates.append({
                    "text": plate,
                    "confidence": 85  # Tesseract doesn't provide confidence scores
                })
        
        # Check database for vehicle info and log detections
        results_with_info = []
        for plate in plates[:3]:
            # Look up vehicle in database using normalized plate
            normalized_detected = normalize_plate_number(plate['text'])
            all_vehicles = db.query(Vehicle).all()
            vehicle = None
            for v in all_vehicles:
                if normalize_plate_number(v.plate_number) == normalized_detected:
                    vehicle = v
                    break
            
            # Log the detection
            detection_log = DetectionLog(
                plate_number=plate['text'].upper(),
                detected_text=plate['text'],
                confidence=plate['confidence'],
                source=source,
                vehicle_id=vehicle.id if vehicle else None
            )
            db.add(detection_log)
            
            # Prepare result with owner info if found
            result = {
                "text": plate['text'],
                "confidence": plate['confidence']
            }
            
            if vehicle:
                result['vehicle_info'] = {
                    "make": vehicle.make,
                    "model": vehicle.model,
                    "year": vehicle.year,
                    "color": vehicle.color,
                    "status": vehicle.status,
                    "owner": {
                        "name": f"{vehicle.owner.first_name} {vehicle.owner.last_name}",
                        "email": vehicle.owner.email,
                        "phone": vehicle.owner.phone,
                        "city": vehicle.owner.city,
                        "state": vehicle.owner.state
                    }
                }
            
            results_with_info.append(result)
        
        db.commit()
        
        return JSONResponse({
            "success": True,
            "plates": results_with_info,
            "source": source
        })
        
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        })

if __name__ == "__main__":
    import uvicorn
    print("Starting License Plate Detection Server...")
    print("Make sure Tesseract is installed: sudo apt-get install tesseract-ocr")
    uvicorn.run(app, host="0.0.0.0", port=8001)