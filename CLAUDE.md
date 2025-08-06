# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a hybrid system combining:
1. **License Plate Detection**: Free, local OCR-based plate detection using Tesseract
2. **Traffic Violation Management**: Complete backend for managing violations, payments, and appeals with role-based access control

The system runs entirely locally without cloud dependencies or API keys.

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

# Set up environment variables
cp .env.example .env
# Edit .env to set JWT_SECRET_KEY
```

### Running the Application
```bash
# Default configured to run on port 8001
python app.py

# Access at: http://localhost:8001
# API documentation: http://localhost:8001/docs
```

### Database Operations
```bash
# Seed original plate detection data
python seed_database.py

# Seed violation system data (users, violation types)
python seed_violation_data.py

# Check database contents
python check_database.py

# Test authentication system
python test_auth.py
```

### Testing
```bash
# Run authentication tests
python test_auth.py

# Test login UI (Selenium-based)
python test_login_ui.py
```

## Architecture

### Technology Stack
- **Backend**: FastAPI, SQLAlchemy, SQLite, JWT authentication
- **OCR**: Tesseract OCR with OpenCV preprocessing
- **Frontend**: HTML/CSS/JavaScript with Jinja2 templates
- **Security**: Bcrypt password hashing, role-based access control

### Core Components

1. **FastAPI Application** (`app.py`)
   - Plate detection with OCR pipeline
   - Complete violation management API
   - JWT-based authentication
   - Role-based endpoint protection (SUPER_ADMIN, OFFICER, CASHIER)
   - Audit logging for all actions

2. **Database Layer** (`database.py`, `schemas.py`)
   - SQLAlchemy ORM with SQLite
   - 9 tables total:
     - Original: `owners`, `vehicles`, `detection_logs`
     - Violation system: `users`, `violation_types`, `violations`, `payments`, `appeals`, `audit_logs`
   - Database stored in `data/plate_detection.db`

3. **Authentication** (`auth.py`)
   - JWT token generation/validation
   - Password hashing with bcrypt
   - Role-based decorators (`@require_role`)
   - Audit logging functions

4. **Frontend** (`templates/`, `static/`)
   - `index.html`: Plate detection interface (functional)
   - `admin.html`: Vehicle/owner management (functional)
   - `login.html`: Authentication page (partially implemented)
   - Missing: Role-specific dashboards for violation management

### API Structure

#### Authentication Endpoints
- `POST /api/auth/login` - User login (returns JWT token)
- `POST /api/auth/logout` - User logout
- `GET /api/auth/me` - Current user information

#### User Management (SUPER_ADMIN only)
- `POST /api/users` - Create new user
- `GET /api/users` - List all users
- `PUT /api/users/{id}` - Update user
- `DELETE /api/users/{id}` - Deactivate user

#### Violation Management
- `POST /api/violations` - Create violation (OFFICER only)
- `GET /api/violations` - List violations (filtered by role)
- `GET /api/violations/ticket/{number}` - Lookup by ticket number
- `PUT /api/violations/{id}/status` - Update status (SUPER_ADMIN only)

#### Payment Processing
- `POST /api/payments` - Process payment (CASHIER only)
- `GET /api/payments` - List payments

#### Appeals
- `POST /api/appeals` - Submit appeal
- `GET /api/appeals` - List appeals
- `PUT /api/appeals/{id}/status` - Update appeal status (SUPER_ADMIN only)

#### Original Plate Detection
- `POST /detect` - Process image/camera/manual input
- `GET/POST /api/owners` - Owner management
- `GET/POST /api/vehicles` - Vehicle management

### Default Credentials

After running `seed_violation_data.py`:
- Super Admin: `admin` / `admin123`
- Officer: `officer1` / `officer123`
- Cashier: `cashier1` / `cashier123`

### Current Implementation Status

**Completed Backend Features:**
- ✅ Full plate detection with OCR
- ✅ JWT authentication system
- ✅ Role-based access control
- ✅ Violation CRUD operations
- ✅ Payment processing
- ✅ Appeal system
- ✅ Audit logging
- ✅ API documentation

**Missing Frontend Features:**
- ❌ Authentication integration with frontend
- ❌ Officer dashboard for creating violations
- ❌ Cashier dashboard for payment processing
- ❌ Admin dashboard for system management
- ❌ Violation lookup interface
- ❌ Report generation UI

### Important Notes

- The app runs on port 8001 (configured to avoid conflicts)
- All API endpoints except `/detect` and auth endpoints require JWT authentication
- Role-based access is strictly enforced on the backend
- Sample plate numbers after seeding: ABC-1234, TEST123, DEF-5678
- Violation types are predefined (V01-V10) with specific fines
- All user actions are logged in the audit_logs table

## Recent Development Progress (July 11, 2025)

### Completed Frontend Implementation

#### 1. Dashboard Infrastructure
- **Base Template** (`templates/dashboard_base.html`): Common layout with sidebar navigation
- **CSS Framework** (`static/dashboard.css`): Complete styling system with CSS variables
- **JavaScript Utilities** (`static/dashboard.js`): Toast notifications, loading states, utilities
- **API Client** (`static/api.js`): Centralized API communication with error handling

#### 2. Role-Specific Dashboards
- **Officer Dashboard** (`templates/officer_dashboard.html`):
  - Statistics cards (today's violations, pending, paid, total fines)
  - Violation creation form with all fields
  - Recent violations table
  - Quick access to plate scanner
  
- **Cashier Dashboard** (`templates/cashier_dashboard.html`):
  - Payment statistics (collections, transactions, pending)
  - Two-step payment process (lookup → payment)
  - Recent payments table
  - Quick ticket search

- **Admin Dashboard** (`templates/admin_dashboard.html`):
  - System overview statistics
  - User management interface
  - Recent activity feed
  - System alerts
  - Placeholder for reports and charts

#### 3. Enhanced Existing Pages
- **Vehicle Registry** (`templates/admin_vehicles_modern.html`):
  - Modern redesign with statistics dashboard
  - Two-column layout (forms + registry list)
  - Real-time search functionality
  - Better visual hierarchy with cards
  
- **Navigation Updates**:
  - Added consistent navigation bar to `index.html` and `admin.html`
  - Dashboard links based on user role
  - Login/logout functionality
  - Authentication state awareness

### What's Next (Priority Order)

#### 1. Complete Missing Features
- **Violation Details View**: Modal to show full violation information
- **Receipt Generation**: PDF receipt for payments
- **Appeals Interface**: UI for submitting and managing appeals
- **Report Generation**: Export violations/payments to PDF/Excel
- **Photo Upload**: Implement actual photo upload for violations

#### 2. Data Visualization
- **Charts for Admin Dashboard**: 
  - Violation trends (line chart)
  - Payment methods distribution (pie chart)
  - Officer performance metrics
- **Real-time Statistics**: Connect mock data to actual database queries

#### 3. Advanced Features
- **Email/SMS Notifications**: 
  - Send violation notices
  - Payment confirmations
- **Batch Operations**: 
  - Bulk violation updates
  - Mass payment processing
- **Advanced Search**: 
  - Date range filters
  - Multiple criteria search
  - Export search results

#### 4. User Experience Improvements
- **Dark Mode**: Theme toggle functionality
- **Responsive Tables**: Better mobile experience
- **Keyboard Shortcuts**: Quick navigation
- **Auto-save Forms**: Prevent data loss
- **Print Stylesheets**: Optimized printing

#### 5. System Enhancements
- **Audit Log Viewer**: UI for viewing system logs
- **Backup/Restore**: Database management interface
- **Settings Page**: System configuration UI
- **Performance Dashboard**: Response times, usage stats

### File Structure Summary
```
/var/www/html/plate/
├── templates/
│   ├── dashboard_base.html      # Base template for all dashboards
│   ├── officer_dashboard.html   # Officer-specific dashboard
│   ├── cashier_dashboard.html   # Cashier-specific dashboard
│   ├── admin_dashboard.html     # Admin-specific dashboard
│   ├── admin_vehicles_modern.html # Modern vehicle registry
│   ├── login.html              # Login page
│   ├── index.html              # Plate scanner (updated with nav)
│   └── admin.html              # Old vehicle registry (deprecated)
├── static/
│   ├── dashboard.css           # Dashboard styling
│   ├── dashboard.js            # Dashboard functionality
│   ├── api.js                  # API client
│   ├── auth.js                 # Authentication utilities
│   ├── login.css               # Login page styles
│   ├── login.js                # Login page logic
│   └── style.css               # Original app styles
└── app.py                      # Updated routes for dashboards