from fastapi import APIRouter, UploadFile, File, Depends
from sqlalchemy.orm import Session
import os

from app.services.file_service import save_file
from app.config import ALLOWED_EXTENSIONS
from database.database import get_db
from database.models import Upload
from detectors.image_preprocessor import analyze_image
from detectors.ela_detector import perform_ela
from detectors.exif_detector import extract_exif
from detectors.noise_detector import detect_noise
from detectors.copy_move_detector import detect_copy_move
from detectors.fusion_engine import calculate_score
from report_generator.pdf_report import generate_pdf_report

router = APIRouter()


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):

    extension = os.path.splitext(file.filename)[1].lower()

    if extension not in ALLOWED_EXTENSIONS:
        return {
            "error": "Unsupported file type"
        }

    saved_name = save_file(file)
    saved_path = os.path.join("uploads", saved_name)

    analysis = {}

    

    if extension in [".jpg", ".jpeg", ".png"]:

        # OpenCV Analysis
        analysis = analyze_image(saved_path)

        # Error Level Analysis
        ela_path = perform_ela(saved_path)
        analysis["ela_report"] = ela_path

        # EXIF Metadata
        exif_data = extract_exif(saved_path)
        analysis["exif"] = exif_data

        # Noise Analysis
        noise_path = detect_noise(saved_path)
        analysis["noise_report"] = noise_path

        # Copy-Move Detection
        copy_move_path = detect_copy_move(saved_path)
        analysis["copy_move_report"] = copy_move_path

    # Final AI Decision
    final_result = calculate_score(analysis)
    # Generate PDF Report
    pdf_report = generate_pdf_report(
        file.filename,
        analysis,
        final_result
    )    

    new_upload = Upload(
        original_filename=file.filename,
        saved_filename=saved_name,
        file_type=extension,
        status="Uploaded"
        
    )

    db.add(new_upload)
    db.commit()
    db.refresh(new_upload)

    return {
    "original_filename": file.filename,
    "saved_filename": saved_name,
    "message": "Upload Successful",

    "analysis": analysis,

    "final_decision": final_result,

    "pdf_report": pdf_report
}