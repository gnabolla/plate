from fastapi import FastAPI, UploadFile, File, Form, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
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
from datetime import datetime

# Import database models and schemas
from database import get_db, Owner, Vehicle, DetectionLog
import schemas

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

os.makedirs("uploads", exist_ok=True)

def preprocess_image(image):
    """Preprocess image for better OCR accuracy"""
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Apply bilateral filter to reduce noise while keeping edges sharp
    gray = cv2.bilateralFilter(gray, 11, 17, 17)
    
    # Find edges in the image
    edged = cv2.Canny(gray, 30, 200)
    
    # Find contours
    cnts = cv2.findContours(edged.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    cnts = imutils.grab_contours(cnts)
    cnts = sorted(cnts, key=cv2.contourArea, reverse=True)[:10]
    
    plate_image = None
    
    # Loop over contours to find license plate
    for c in cnts:
        # Approximate the contour
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.018 * peri, True)
        
        # If contour has 4 points, it might be a license plate
        if len(approx) == 4:
            x, y, w, h = cv2.boundingRect(approx)
            aspect_ratio = w / float(h)
            
            # License plates typically have aspect ratio between 2:1 and 5:1
            if 2.0 <= aspect_ratio <= 5.0:
                plate_image = gray[y:y+h, x:x+w]
                break
    
    # If no plate-like contour found, process the whole image
    if plate_image is None:
        plate_image = gray
    
    # Resize for better OCR
    plate_image = cv2.resize(plate_image, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    
    # Apply threshold to get black text on white background
    _, plate_image = cv2.threshold(plate_image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    # Denoise
    plate_image = cv2.medianBlur(plate_image, 3)
    
    return plate_image

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
    # Check if plate already exists
    existing = db.query(Vehicle).filter(Vehicle.plate_number == vehicle.plate_number).first()
    if existing:
        raise HTTPException(status_code=400, detail="Plate number already registered")
    
    db_vehicle = Vehicle(**vehicle.dict())
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
            print(f"Searching for plate: {plate_upper}")  # Debug
            vehicle = db.query(Vehicle).filter(Vehicle.plate_number == plate_upper).first()
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
            except:
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
        except:
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
            # Look up vehicle in database
            vehicle = db.query(Vehicle).filter(Vehicle.plate_number == plate['text'].upper()).first()
            
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