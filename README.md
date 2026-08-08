# AI Media Integrity Detector

AI Media Integrity Detector is a Python-based project for checking images for possible signs of manipulation.

The project uses different image forensic techniques and combines their results to give an overall assessment of the uploaded image. It also generates a PDF report containing the analysis results.

## Project Overview

The current system works as follows:

User uploads an image
        ↓
FastAPI backend
        ↓
Image analysis
        ↓
ELA + EXIF + Noise + Copy-Move analysis
        ↓
Fusion Engine
        ↓
Final prediction
        ↓
PDF report

## Features

- Image upload using FastAPI
- Image information extraction
- EXIF metadata extraction
- Error Level Analysis (ELA)
- Noise analysis
- Copy-Move detection
- Fusion-based scoring
- Confidence score
- PDF report generation
- SQLite database for storing upload information

## Forensic Analysis

### Error Level Analysis

ELA is used to examine differences in JPEG compression levels in different parts of an image. The project generates an ELA image that can be checked as part of the analysis.

### EXIF Metadata

The project extracts available metadata from the image, including:

- Camera make
- Camera model
- Date and time
- Image dimensions
- ISO
- Aperture
- Exposure time
- Focal length

### Noise Analysis

Noise analysis is performed on the uploaded image and a separate noise report is generated.

### Copy-Move Detection

Copy-Move Detection is used to check whether similar regions are present in different parts of the image.

## Final Decision

The Fusion Engine uses the available analysis results to calculate a score and produce a final prediction.

The result currently contains:

- Prediction
- Confidence
- Reasons

The prediction is treated as an indication from the available forensic analysis, not as final proof that an image is genuine or manipulated.

## PDF Report

The report also shows the status of the forensic analysis and the final integrity assessment.
After the analysis is completed, the system generates a PDF report.


The report contains:

- Original file name
- Image information
- EXIF information
- Forensic analysis status
- Final prediction
- Confidence
- Reasons
- Project information

Example:

Error Level Analysis    Completed
Noise Analysis          Completed
Copy-Move Detection     Completed

## Project Structure

```text
AI-Media-Integrity-Detector/
│
├── backend/
│   ├── app/
│   │   ├── routers/
│   │   │   ├── health.py
│   │   │   └── upload.py
│   │   │
│   │   └── services/
│   │       └── file_service.py
│   │
│   ├── database/
│   │   ├── database.py
│   │   └── models.py
│   │
│   ├── detectors/
│   │   ├── copy_move_detector.py
│   │   ├── ela_detector.py
│   │   ├── exif_detector.py
│   │   ├── fusion_engine.py
│   │   ├── image_preprocessor.py
│   │   └── noise_detector.py
│   │
│   ├── report_generator/
│   │   └── pdf_report.py
│   │
│   ├── main.py
│   └── requirements.txt
│
├── frontend/
├── docs/
├── .gitignore
└── README.md
```

## Technologies Used

- Python
- FastAPI
- OpenCV
- Pillow
- SQLAlchemy
- SQLite
- ReportLab
- Uvicorn
- Git and GitHub

## Running the Project

Clone the repository:

git clone https://github.com/ramesh9601/AI-Media-Integrity-Detector.git

Go to the backend:

cd AI-Media-Integrity-Detector/backend

Create a virtual environment:

python -m venv venv

Activate it on Windows:

venv\Scripts\activate

Install the required packages:

pip install -r requirements.txt

Start the server:

uvicorn main:app --reload

Open the API documentation:

http://127.0.0.1:8000/docs

## API

The main upload endpoint is:

POST /upload

An image can be uploaded through the FastAPI Swagger interface.

The response contains the image analysis, forensic report paths, final decision and generated PDF report.

## Current Status

The backend and initial image forensic analysis pipeline are working.

Implemented:

- Image upload
- Image preprocessing
- ELA
- EXIF extraction
- Noise analysis
- Copy-Move detection
- Fusion scoring
- PDF report generation

## Future Work

The project will be extended with:

- Deep learning based image detection
- Better manipulation scoring
- Video analysis
- Frontend dashboard
- Analysis history
- Media provenance checking
- Deployment

## Developer

NALLABELLI RAMESH

M.Sc Computer Science

AI Media Integrity Detector
Version 1.0

Development branch: Deepfake Detection