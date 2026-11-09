import cv2
import os
import logging
import tempfile

logger = logging.getLogger(__name__)

# This threshold is provisional, not empirically validated.
PROVISIONAL_CLASSIFICATION_THRESHOLD = 0.50
MODEL_NAME = "CommunityForensics-DeepfakeDet-ViT"


def analyze_video(
    video_path,
    output_folder="reports",
    frame_interval=1,
    max_frames=30
):
    """
    Extract video frames and screen them using an ONNX
    AI-generated-image detection model.

    Frame-level model scores do not prove whether a video
    is authentic or manipulated.
    """
    if not os.path.isfile(video_path):
        raise FileNotFoundError("Video file not found.")

    if frame_interval <= 0:
        raise ValueError("Frame interval must be greater than zero.")

    if max_frames <= 0:
        raise ValueError("Maximum frames must be greater than zero.")

    os.makedirs(output_folder, exist_ok=True)
    video = cv2.VideoCapture(video_path)

    if not video.isOpened():
        raise ValueError("Unable to open video file.")

    fps = video.get(cv2.CAP_PROP_FPS)
    total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
    duration = total_frames / fps if fps > 0 else 0

    extracted_frames = []
    frame_predictions = []
    failed_frames = []
    model_error = None

    frame_folder = tempfile.mkdtemp(prefix="video_frames_", dir=output_folder)
    video_name = os.path.basename(video_path)
    frame_number = 0
    saved_count = 0
    interval = max(1, round(fps * frame_interval)) if fps > 0 else 1

    try:
        while saved_count < max_frames:
            success, frame = video.read()
            if not success:
                break

            if frame_number % interval == 0:
                frame_filename = f"frame_{saved_count:04d}.jpg"
                frame_path = os.path.join(frame_folder, frame_filename)

                if cv2.imwrite(frame_path, frame):
                    extracted_frames.append({
                        "path": frame_path,
                        "frame_number": frame_number,
                        "timestamp_seconds": round(frame_number / fps, 3) if fps > 0 else None,
                    })
                    saved_count += 1
                else:
                    failed_frames.append({
                        "frame_number": frame_number,
                        "error": "Unable to save extracted frame.",
                    })
            frame_number += 1
    finally:
        video.release()

    if extracted_frames:
        try:
            from detectors.deepfake_onnx_detector import detect_deepfake_image

            for frame_info in extracted_frames:
                frame_path = frame_info["path"]
                try:
                    result = detect_deepfake_image(frame_path)
                    fake_score = float(result["fake_probability"])
                    real_score = float(result["real_probability"])

                    if not 0.0 <= fake_score <= 1.0:
                        raise ValueError("Detector returned a score outside the 0–1 range.")

                    # Use the detector's prediction, but count threshold crossings
                    # separately so the report can explain both values.
                    frame_predictions.append({
                        "frame": os.path.basename(frame_path),
                        "frame_number": frame_info["frame_number"],
                        "timestamp_seconds": frame_info["timestamp_seconds"],
                        "prediction": result.get("prediction", "Unknown"),
                        "fake_probability": fake_score,
                        "real_probability": real_score,
                    })
                except Exception as exc:
                    logger.exception("Failed to analyze frame: %s", frame_path)
                    failed_frames.append({
                        "frame": os.path.basename(frame_path),
                        "frame_number": frame_info["frame_number"],
                        "timestamp_seconds": frame_info["timestamp_seconds"],
                        "error": str(exc),
                    })
        except Exception as exc:
            logger.exception("Unable to initialize ONNX detector.")
            model_error = str(exc)
            for frame_info in extracted_frames:
                failed_frames.append({
                    "frame": os.path.basename(frame_info["path"]),
                    "frame_number": frame_info["frame_number"],
                    "timestamp_seconds": frame_info["timestamp_seconds"],
                    "error": "ONNX detector initialization failed.",
                })

    analyzed_count = len(frame_predictions)
    failed_count = len(failed_frames)

    if analyzed_count > 0:
        fake_scores = [item["fake_probability"] for item in frame_predictions]
        real_scores = [item["real_probability"] for item in frame_predictions]
        average_fake_probability = sum(fake_scores) / analyzed_count
        average_real_probability = sum(real_scores) / analyzed_count
        highest_score_frame = max(frame_predictions, key=lambda item: item["fake_probability"])

        frames_above_threshold = sum(
            1 for item in frame_predictions
            if item["fake_probability"] >= PROVISIONAL_CLASSIFICATION_THRESHOLD
        )
        ai_generated_like_frames = sum(
            1 for item in frame_predictions
            if item["prediction"] == "AI-Generated-Like"
        )
        analysis_status = "partial" if failed_count > 0 or model_error else "completed"

        summary = {
            "analysis_status": analysis_status,
            "frames_extracted": saved_count,
            "frames_analyzed": analyzed_count,
            "frames_failed": failed_count,
            "sampling_interval_seconds": frame_interval,
            "maximum_frames": max_frames,
            "average_fake_probability": round(average_fake_probability, 8),
            "average_real_probability": round(average_real_probability, 8),
            "highest_scoring_frame": highest_score_frame["frame"],
            "highest_frame_number": highest_score_frame["frame_number"],
            "highest_frame_timestamp_seconds": highest_score_frame["timestamp_seconds"],
            "highest_frame_fake_probability": highest_score_frame["fake_probability"],
            "ai_generated_like_frames": ai_generated_like_frames,
            "provisional_classification_threshold": PROVISIONAL_CLASSIFICATION_THRESHOLD,
            "frames_above_provisional_threshold": frames_above_threshold,
            "threshold_status": "provisional_not_validated",
            "threshold_note": (
                "The 50% threshold is provisional and has not been validated "
                "against a representative evaluation dataset."
            ),
            "model": MODEL_NAME,
        }
    else:
        summary = {
            "analysis_status": "failed",
            "frames_extracted": saved_count,
            "frames_analyzed": 0,
            "frames_failed": failed_count,
            "sampling_interval_seconds": frame_interval,
            "maximum_frames": max_frames,
            "provisional_classification_threshold": PROVISIONAL_CLASSIFICATION_THRESHOLD,
            "threshold_status": "provisional_not_validated",
            "threshold_note": "The 50% threshold is provisional and has not been validated.",
            "message": "No frames could be analyzed by the ONNX model.",
        }

    response = {
        "video_filename": video_name,
        "video_width": width,
        "video_height": height,
        "fps": round(fps, 2),
        "total_frames": total_frames,
        "duration_seconds": round(duration, 2),
        "frames_extracted": saved_count,
        "frames_analyzed": analyzed_count,
        "frames_failed": failed_count,
        "extracted_frames": [item["path"] for item in extracted_frames],
        "analysis_type": "Video frame AI-generated-image screening",
        "deepfake_detected": None,
        "frame_analysis": frame_predictions,
        "failed_frame_details": failed_frames,
        "detection_summary": summary,
        "message": (
            "Selected video frames were screened using an AI-generated-image "
            "detection model. These estimates do not establish whether the "
            "complete video is authentic or manipulated."
        ),
    }
    if model_error:
        response["model_error"] = model_error
    return response
