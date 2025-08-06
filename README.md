# License Plate Detection & Traffic Violation Management System

A comprehensive web-based system that combines automatic license plate detection with a complete traffic violation management workflow. The system uses OCR technology for plate recognition and includes role-based dashboards for officers, cashiers, and administrators.

## Features

### License Plate Detection
- **OCR-based detection** using Tesseract
- **Multiple input sources**: Upload image, camera capture, or manual entry
- **Real-time processing** with visual feedback
- **Vehicle registry** integration

### Traffic Violation Management
- **Role-based access control** (Super Admin, Officer, Cashier)
- **JWT authentication** with secure session management
- **Complete violation workflow**: Create → Issue → Pay → Appeal
- **Audit logging** for all system actions
- **Modern dashboards** for each user role

## Quick Start

### Prerequisites
- Python 3.8+
- Tesseract OCR
- Git

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd plate
```

2. **Set up Python environment**
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install system dependencies**
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install tesseract-ocr

# macOS
brew install tesseract

# Windows
# Download installer from: https://github.com/UB-Mannheim/tesseract/wiki
```

4. **Install Python dependencies**
```bash
pip install -r requirements.txt
```

5. **Configure environment**
```bash
cp .env.example .env
# Edit .env and set a secure JWT_SECRET_KEY
```

6. **Initialize database**
```bash
# Create database directory
mkdir -p data

# Seed initial data
python seed_database.py        # Vehicle registry data
python seed_violation_data.py  # Users and violation types
```

7. **Run the application**
```bash
python app.py
```

The application will be available at `http://localhost:8001`

## Default Credentials

After seeding the database:
- **Super Admin**: `admin` / `admin123`
- **Officer**: `officer1` / `officer123`
- **Cashier**: `cashier1` / `cashier123`

## Usage Guide

### For Officers
1. Login with officer credentials
2. Access the Officer Dashboard
3. Create violations using the plate scanner or manual entry
4. Track issued violations and their status

### For Cashiers
1. Login with cashier credentials
2. Access the Cashier Dashboard
3. Look up violations by ticket number
4. Process payments and generate receipts

### For Administrators
1. Login with admin credentials
2. Access the Admin Dashboard
3. Manage users and system settings
4. View system-wide statistics and reports
5. Handle violation appeals

## API Documentation

Once the application is running, access the interactive API documentation at:
- Swagger UI: `http://localhost:8001/docs`
- ReDoc: `http://localhost:8001/redoc`

## Project Structure

```
plate/
├── app.py                    # Main FastAPI application
├── database.py               # Database models
├── schemas.py                # Pydantic schemas
├── auth.py                   # Authentication logic
├── requirements.txt          # Python dependencies
├── .env.example             # Environment variables template
├── templates/               # HTML templates
│   ├── index.html          # Plate scanner
│   ├── login.html          # Login page
│   ├── dashboard_base.html # Dashboard template
│   ├── officer_dashboard.html
│   ├── cashier_dashboard.html
│   └── admin_dashboard.html
├── static/                  # CSS, JS, images
│   ├── api.js              # API client
│   ├── auth.js             # Auth utilities
│   ├── dashboard.css       # Dashboard styles
│   └── dashboard.js        # Dashboard logic
└── data/                   # SQLite database (created on first run)
```

## Development

### Running Tests
```bash
# Test authentication system
python test_auth.py

# Test UI components (requires Selenium)
python test_login_ui.py
```

### Database Management
```bash
# Check database contents
python check_database.py

# Reset database
rm data/plate_detection.db
python seed_database.py
python seed_violation_data.py
```

## Security Considerations

- Change default passwords immediately in production
- Set a strong `JWT_SECRET_KEY` in `.env`
- Use HTTPS in production environments
- Regularly backup the database
- Review audit logs for suspicious activity

## Troubleshooting

### Common Issues

1. **Port 8001 already in use**
   - Change the port in `app.py` or stop the conflicting service

2. **Tesseract not found**
   - Ensure Tesseract is installed and in your system PATH
   - On Windows, you may need to specify the path in the code

3. **Database errors**
   - Ensure the `data/` directory exists and has write permissions
   - Try deleting the database and re-running seed scripts

4. **Login issues**
   - Clear browser cookies/cache
   - Ensure you're using the correct credentials
   - Check that JWT_SECRET_KEY is set in `.env`

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Support

For issues, questions, or contributions, please open an issue on the GitHub repository.