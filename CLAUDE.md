# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a free, local license plate detection web application using Tesseract OCR. It provides plate detection through image upload, camera capture, or manual input, with an integrated SQLite database for storing owner and vehicle information.

## Development Commands

### Environment Setup
```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install system dependency (Tesseract OCR)
sudo apt-get update
sudo apt-get install tesseract-ocr

# Install Python dependencies
pip install -r requirements.txt
```

### Running the Application
```bash
# Default port 8000
python app.py

# The app is configured to use port 8001 due to conflicts
# Access at: http://localhost:8001
```

### Database Operations
```bash
# Seed database with sample data
python seed_database.py

# Check database contents
python check_database.py
```

## Architecture

### Core Components

1. **FastAPI Backend** (`app.py`)
   - Main application with OCR processing pipeline
   - Image preprocessing using OpenCV (grayscale, filtering, contour detection)
   - Multiple Tesseract OCR configurations for better accuracy
   - Database integration for vehicle/owner lookup
   - Detection logging for all plate reads

2. **Database Layer** (`database.py`, `schemas.py`)
   - SQLAlchemy ORM with SQLite
   - Three main tables:
     - `owners`: Contact information
     - `vehicles`: Plate numbers linked to owners
     - `detection_logs`: History of all detections
   - Database stored in `data/plate_detection.db`

3. **Frontend** (`templates/`, `static/`)
   - Main detection interface (`index.html`)
   - Admin panel for data entry (`admin.html`)
   - JavaScript handles file uploads, camera access, and API calls
   - Results display vehicle/owner info when plates are found in database

### Key Processing Flow

1. **Image Detection Pipeline**:
   - Preprocess image (grayscale, bilateral filter, edge detection)
   - Find contours and identify plate-like rectangles
   - Apply multiple Tesseract PSM modes for text extraction
   - Pattern matching for common plate formats
   - Database lookup for owner information
   - Log all detections

2. **API Endpoints**:
   - `POST /detect` - Main detection endpoint (handles all input types)
   - `GET/POST /api/owners` - Owner management
   - `GET/POST /api/vehicles` - Vehicle registration
   - `GET /admin` - Admin interface

## Important Notes

- The app checks the database for ALL input types (upload, camera, manual)
- Detection results show up to 3 candidates with confidence scores
- All detections are logged with timestamps and source type
- Sample plate numbers after seeding: ABC-1234, TEST123, DEF-5678
- Database must be seeded before owner info will display