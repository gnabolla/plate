# Free License Plate Detection

100% free, local license plate detection using Tesseract OCR. No API keys, no cloud services, no fees.

## Features

- **100% Free** - Uses open-source Tesseract OCR
- **Local Processing** - All detection happens on your machine
- **No API Keys** - No registration or fees required
- **Lightweight** - Under 200MB total
- **Multiple Input Methods**:
  - Upload images
  - Use camera
  - Manual input

## Prerequisites

Install Tesseract OCR:
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr
```

## Installation

1. Create virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Run the application:
```bash
python app.py
```

2. Open browser:
```
http://localhost:8000
```

## How It Works

1. **Image Preprocessing**: Converts to grayscale, applies filters, finds contours
2. **Plate Detection**: Looks for rectangular shapes with license plate aspect ratios
3. **OCR**: Uses Tesseract with multiple configurations to read text
4. **Pattern Matching**: Extracts common license plate patterns

## Accuracy

- Works best with clear, well-lit images
- Front-facing plates work better than angled ones
- Preprocessing helps with challenging images

## Total Size

- Python dependencies: ~150MB
- Tesseract: ~50MB
- **Total: ~200MB** (vs 5.5GB for deep learning solutions!)

No hidden costs, no API limits, no cloud dependencies. Just free, local license plate detection.