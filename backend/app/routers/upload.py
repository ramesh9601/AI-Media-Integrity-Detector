import logging
logger = logging.getLogger(__name__)
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import os

from app.services.file_service import save_file
from app.services.cloudinary_service import upload_to_cloudinary
from app.config import ALLOWED_EXTENSIONS
from database.database import get_db
from database.models import Upload, User
from app.routers.auth import (
    get_current_user,
    get_optional_current_user
)

from detectors.image_preprocessor import analyze_image
from detectors.ela_detector import perform_ela
from detectors.deepfake_onnx_detector import detect_deepfake_image
from detectors.exif_detector import extract_exif
from detectors.noise_detector import detect_noise
from detectors.copy_move_detector import detect_copy_move
from detectors.video_preprocessor import analyze_video

from detectors.fusion_engine import (
    calculate_score,
    calculate_video_score
)

from report_generator.pdf_report import generate_pdf_report
from app.schemas.upload import UploadResponse
from app.limiter import limiter

router = APIRouter()


# ------------------------------------------
# Upload and Analyze Media
# ------------------------------------------

@router.post("/upload", response_model=UploadResponse)
@limiter.limit("10/minute")
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_optional_current_user)
):
    # Get file extension
    extension = os.path.splitext(file.filename)[1].lower()

    # Validate file type
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type."
        )

    # Save uploaded file
    try:
        saved_name = save_file(file)

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    saved_path = os.path.join("uploads", saved_name)

    # Store all analysis results
    analysis = {}

    # ------------------------------------------
    # IMAGE ANALYSIS
    # ------------------------------------------

    if extension in [".jpg", ".jpeg", ".png"]:

        # Image preprocessing
        try:
            analysis = analyze_image(saved_path)

        except Exception:
            logger.exception("Image preprocessing failed")

            analysis["image_analysis"] = {
                "status": "Unavailable",
                "error": "Image preprocessing could not be completed."
            }

        # AI-generated image detection
        try:
            ai_result = detect_deepfake_image(saved_path)

            if not isinstance(ai_result, dict):
                raise TypeError(
                    "The AI detector returned an unexpected result format."
                )

            ai_result.setdefault("status", "Completed")
            ai_result.setdefault(
                "warning",
                "These are model scores, not proof of authenticity "
                "or manipulation."
            )

            analysis["ai_detection"] = ai_result

        except Exception:
            logger.exception("AI image detection failed")

            analysis["ai_detection"] = {
                "status": "Unavailable",
                "error": "AI image detection could not be completed.",
                "warning": (
                    "AI-generated image detection could not be "
                    "completed. Do not interpret this as evidence "
                    "that the image is authentic or manipulated."
                )
            }

        # Error Level Analysis
        try:
            ela_result = perform_ela(saved_path)

            analysis["ela"] = ela_result
            analysis["ela_report"] = ela_result.get("report")

        except Exception:
            logger.exception("ELA analysis failed")

            analysis["ela"] = {
                "status": "Unavailable",
                "score": 50,
                "details": "ELA analysis could not be completed.",
                "error": "ELA analysis is temporarily unavailable."
            }

        # EXIF metadata analysis
        try:
            analysis["exif"] = extract_exif(saved_path)

        except Exception:
            logger.exception("EXIF metadata analysis failed")

            analysis["exif"] = {}
            analysis["exif_error"] = (
            "EXIF metadata analysis could not be completed."
        )

        # Noise analysis
        try:
            noise_result = detect_noise(saved_path)

            analysis["noise"] = noise_result
            analysis["noise_report"] = noise_result.get("report")

        except Exception:
            logger.exception("Noise analysis failed")

            analysis["noise"] = {
                "status": "Unavailable",
                "score": 50,
                "details": "Noise analysis could not be completed.",
                "error": "Noise analysis is temporarily unavailable."
            }

        # Copy-move detection
        try:
            copy_move_result = detect_copy_move(saved_path)

            analysis["copy_move"] = copy_move_result
            analysis["copy_move_report"] = (
                copy_move_result.get("report")
            )

        except Exception:
            logger.exception("Copy-move detection failed")

            analysis["copy_move"] = {
                "status": "Unavailable",
                "score": 50,
                "matches": 0,
                "details": "Copy-move analysis could not be completed.",
                "error": "Copy-move detection is temporarily unavailable."
            }



    # ------------------------------------------
    # VIDEO ANALYSIS
    # ------------------------------------------

    elif extension in [".mp4", ".avi", ".mov"]:

        try:
            analysis["video"] = analyze_video(
                saved_path,
                output_folder="reports/debug_video_frames"
            )

        except Exception:
            logger.exception("Video analysis failed")

            analysis["video"] = {
                "detection_summary": {
                "analysis_status": "failed",
                "frames_analyzed": 0
            },
            "error": "Video analysis could not be completed."
        }


    # ------------------------------------------
    # FINAL ASSESSMENT
    # ------------------------------------------

    if extension in [".jpg", ".jpeg", ".png"]:

        # Existing image detection system
        final_result = calculate_score(analysis)

    elif extension in [".mp4", ".avi", ".mov"]:

        # Calculate provisional video screening estimate
        video_data = analysis.get("video", {})

        final_result = calculate_video_score(video_data)

    else:

        # Unsupported file type
        final_result = {
            "prediction": "Unsupported Media Type",
            "integrity_score": None,
            "color": "gray",
            "reasons": [
                "No assessment method is configured for this file type."
            ]
        }

    # ------------------------------------------
    # NORMALIZE INTEGRITY SCORE
    # ------------------------------------------

    integrity_score = final_result.get("integrity_score")

    if integrity_score is None:
        integrity_score = final_result.get("confidence")

    # ------------------------------------------
    # GENERATE PDF REPORT
    # ------------------------------------------

    try:
        pdf_report = generate_pdf_report(
            file.filename,
            analysis,
            final_result
        )

    except Exception:
        logger.exception("PDF report generation failed")

        raise HTTPException(
            status_code=500,
            detail="PDF report generation failed. Please try again later."
        )
    # ------------------------------------------
    # CLOUDINARY STORAGE
    # ------------------------------------------

    media_url = None
    media_public_id = None
    report_public_id = None
    storage_warnings = []

    # Upload original image or video
    try:
        if extension in [".jpg", ".jpeg", ".png"]:
            resource_type = "image"

        elif extension in [".mp4", ".avi", ".mov"]:
            resource_type = "video"

        else:
            resource_type = None
            storage_warnings.append(
                "Original audio media storage is not configured."
            )

        if resource_type:
            media_result = upload_to_cloudinary(
                saved_path,
                resource_type=resource_type,
                folder="media_integrity/media"
            )

            media_url = media_result["url"]
            media_public_id = media_result["public_id"]

    except Exception:
        logger.exception("Media cloud storage failed")

        storage_warnings.append(
            "Media cloud storage failed. "
            "Please try again later."
        )

    # Upload generated PDF report
    try:
        report_result = upload_to_cloudinary(
            pdf_report,
            resource_type="raw",
            folder="media_integrity/reports",
            delivery_type="private"
        )

        report_public_id = report_result["public_id"]

    except Exception:
        logger.exception("PDF cloud storage failed")

        storage_warnings.append(
            "PDF cloud storage failed. "
            "Please try again later."
        )

    # ------------------------------------------
    # SAVE ANALYSIS ONLY FOR LOGGED-IN USERS
    # ------------------------------------------

    if current_user is not None:

        new_upload = Upload(
            user_id=current_user.id,
            original_filename=file.filename,
            saved_filename=saved_name,
            file_type=extension,
            status=(
                "Completed"
                if final_result.get("integrity_score") is not None
                else "Incomplete"
            ),
            integrity_score=integrity_score,
            prediction=final_result.get(
                "prediction",
                "Unknown"
            ),
            report_path=None,
            report_public_id=report_public_id,
            media_url=media_url,
            media_public_id=media_public_id
        )

        try:
            db.add(new_upload)
            db.commit()
            db.refresh(new_upload)

        except SQLAlchemyError as error:
            db.rollback()

            logger.exception(
                "Failed to save upload analysis to database: %s",
                error
            )

            print("DATABASE ERROR TYPE:", type(error).__name__)
            print("DATABASE ERROR DETAILS:", repr(error))

            raise HTTPException(
                status_code=500,
                detail=(
                    "Analysis completed, but the result could not "
                    "be saved. Please try again later."
                )
            )

    # Guest users are not saved in the database.
    # Their analysis and PDF report are still returned.

    # ------------------------------------------
    # API RESPONSE
    # ------------------------------------------

    return {
        "success": True,
        "message": (
            "Analysis completed and cloud storage successful."
            if not storage_warnings
            else "Analysis completed, but cloud storage was incomplete: "
                 + "; ".join(storage_warnings)
        ),

        "file": {
            "original_name": file.filename,
            "saved_name": saved_name,
            "file_type": extension
        },

        "result": {
            "prediction": final_result.get(
                "prediction",
                "Unknown"
            ),
            "integrity_score": integrity_score,
            "color": final_result.get(
                "color",
                "black"
            ),
            "reasons": final_result.get(
                "reasons",
                []
            )
        },

        "forensics": {
            "image": {
                "width": analysis.get("width"),
                "height": analysis.get("height"),
                "channels": analysis.get("channels"),
                "image_type": analysis.get("image_type"),
                "aspect_ratio": analysis.get("aspect_ratio"),
                "resolution_status": analysis.get(
                    "resolution_status"
                ),
                "file_size_bytes": analysis.get(
                    "file_size_bytes"
                )
            },

            "ai_detection": analysis.get("ai_detection", {}),
            "exif": analysis.get("exif", {}),
            "ela": analysis.get("ela", {}),
            "noise": analysis.get("noise", {}),
            "copy_move": analysis.get("copy_move", {}),
            "video": analysis.get("video", {})
        },

        "report": {
            "pdf": pdf_report
        }
    }


# ------------------------------------------
# LOGGED-IN USER'S ANALYSIS HISTORY
# ------------------------------------------

@router.get("/history")
def get_analysis_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    uploads = (
        db.query(Upload)
        .filter(Upload.user_id == current_user.id)
        .order_by(Upload.id.desc())
        .all()
    )

    return {
        "success": True,
        "total": len(uploads),

        "history": [
            {
                "id": upload.id,
                "original_filename": upload.original_filename,
                "saved_filename": upload.saved_filename,
                "file_type": upload.file_type,
                "status": upload.status,
                "integrity_score": upload.integrity_score,
                "prediction": upload.prediction,
                "report_path": upload.report_path
            }
            for upload in uploads
        ]
    }