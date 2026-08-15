from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
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

        raise HTTPException(
            status_code=400,
            detail="Unsupported file type."
        )

    try:
        saved_name = save_file(file)

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    saved_path = os.path.join(
        "uploads",
        saved_name
    )

    analysis = {}

    

    if extension in [".jpg", ".jpeg", ".png"]:

    # ------------------------------------------
    # Image Preprocessing
    # ------------------------------------------

        try:

            analysis = analyze_image(
                saved_path
            )

        except Exception as error:

            analysis["image_analysis"] = {
                "status": "Unavailable",
                "error": str(error)
            }

    # ------------------------------------------
    # Error Level Analysis
    # ------------------------------------------

        try:

            ela_result = perform_ela(
                saved_path
            )

            analysis["ela"] = ela_result
            analysis["ela_report"] = (
                ela_result.get("report")
            )

        except Exception as error:

            analysis["ela"] = {
                "status": "Unavailable",
                "score": 50,
                "details": (
                    "ELA analysis could not be completed."
                ),
                "error": str(error)
            }

    # ------------------------------------------
    # EXIF Metadata
    # ------------------------------------------

        try:

            exif_data = extract_exif(
                saved_path
            )

            analysis["exif"] = exif_data

        except Exception as error:

            analysis["exif"] = {}

            analysis["exif_error"] = str(error)

    # ------------------------------------------
    # Noise Analysis
    # ------------------------------------------

        try:

            noise_result = detect_noise(
                saved_path
            )

            analysis["noise"] = noise_result
            analysis["noise_report"] = (
                noise_result.get("report")
            )

        except Exception as error:

            analysis["noise"] = {
                "status": "Unavailable",
                "score": 50,
                "details": (
                    "Noise analysis could not be completed."
                ),
                "error": str(error)
            }

    # ------------------------------------------
    # Copy-Move Detection
    # ------------------------------------------

        try:

            copy_move_result = detect_copy_move(
                saved_path
            )

            analysis["copy_move"] = (
                copy_move_result
            )

            analysis["copy_move_report"] = (
                copy_move_result.get("report")
            )

        except Exception as error:

            analysis["copy_move"] = {
                "status": "Unavailable",
                "score": 50,
                "matches": 0,
                "details": (
                    "Copy-move analysis could not "
                    "be completed."
                ),
                "error": str(error)
            }

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