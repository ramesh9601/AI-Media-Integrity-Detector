def calculate_score(analysis):
    """
    Calculate a preliminary forensic assessment score.

    This score is a heuristic, not a probability of authenticity.
    It must not be used alone to confirm or rule out manipulation.

    Existing response fields are preserved for compatibility.
    """

    score = 100.0
    reasons = []

    # ==========================================
    # EXIF METADATA
    # ==========================================

    exif = analysis.get("exif", {})

    if isinstance(exif, dict) and exif:
        reasons.append(
            "EXIF metadata is available. "
            "Its presence does not prove authenticity."
        )
    else:
        reasons.append(
            "No EXIF metadata found. "
            "Missing metadata is not proof of manipulation."
        )

    # Do not reduce the score because EXIF is missing.

    # ==========================================
    # IMAGE RESOLUTION
    # ==========================================

    width = analysis.get("width", 0)
    height = analysis.get("height", 0)

    if (
        isinstance(width, (int, float))
        and isinstance(height, (int, float))
        and width > 0
        and height > 0
    ):
        if width < 500 or height < 500:
            reasons.append(
                "The image has relatively low resolution. "
                "This may limit forensic analysis."
            )
        else:
            reasons.append(
                "Image dimensions are available for analysis."
            )
    else:
        reasons.append(
            "Image dimensions are unavailable or invalid."
        )

    # Resolution alone does not establish authenticity.

    # ==========================================
    # FILE SIZE
    # ==========================================

    file_size = analysis.get("file_size_bytes", 0)

    if isinstance(file_size, (int, float)) and file_size > 0:
        if file_size < 100000:
            reasons.append(
                "The file is smaller than 100 KB. "
                "File size alone is not evidence of manipulation."
            )
    else:
        reasons.append(
            "File size information is unavailable."
        )

    # Do not reduce the score based on file size alone.

    # ==========================================
    # ELA ANALYSIS
    # ==========================================

    ela = analysis.get("ela", {})
    ela_status = "Unavailable"

    if isinstance(ela, dict) and ela:
        ela_status = str(
            ela.get("status", "Unknown")
        ).strip().lower()

        ela_details = ela.get("details")

        if ela_details:
            reasons.append(
                f"ELA analysis: {ela_details}"
            )

        # The detector's score is a heuristic indicator.
        # Apply a limited penalty only for elevated findings.

        if ela_status in ("elevated", "high"):
            score -= 5

            reasons.append(
                "ELA reported elevated differences. "
                "These differences require interpretation and "
                "do not independently prove manipulation."
            )

        elif ela_status == "moderate":
            score -= 2

            reasons.append(
                "Moderate ELA differences were reported. "
                "Compression and image processing can affect ELA."
            )

        elif ela_status == "low":
            reasons.append(
                "ELA reported low compression differences. "
                "This does not rule out manipulation."
            )

        else:
            reasons.append(
                "ELA returned an unrecognized status. "
                "Its result was not used to adjust the score."
            )

    else:
        reasons.append(
            "ELA analysis was unavailable."
        )

    # ==========================================
    # NOISE ANALYSIS
    # ==========================================

    noise = analysis.get("noise", {})

    if isinstance(noise, dict) and noise:
        noise_status = noise.get("status", "Unknown")
        noise_details = noise.get("details")

        if noise_details:
            reasons.append(
                f"Noise analysis: {noise_details}"
            )

        reasons.append(
            f"Reported noise status: {noise_status}. "
            "Laplacian variance measures local intensity variation "
            "and image detail; it is not a direct deepfake probability."
        )

        # Do not penalize the score using noise status alone.

    else:
        reasons.append(
            "Noise analysis was unavailable."
        )

    # ==========================================
    # COPY-MOVE ANALYSIS
    # ==========================================

    copy_move = analysis.get("copy_move", {})

    if isinstance(copy_move, dict) and copy_move:
        copy_move_details = copy_move.get("details")

        if copy_move_details:
            reasons.append(
                f"Copy-move analysis: {copy_move_details}"
            )

        matches = copy_move.get("matches")

        if isinstance(matches, (int, float)):
            reasons.append(
                f"Reported copy-move matches: {matches}."
            )

        reasons.append(
            "Copy-move findings depend on the detection method. "
            "No detected matches does not prove that an image "
            "is authentic."
        )

        # Do not assume the detector's score is a calibrated
        # probability or apply an unsupported numerical penalty.

    else:
        reasons.append(
            "Copy-move analysis was unavailable."
        )

    # ==========================================
    # AI DETECTOR
    # ==========================================

    ai_detection = analysis.get("ai_detection", {})

    if isinstance(ai_detection, dict) and ai_detection:
        ai_prediction = ai_detection.get("prediction")
        fake_probability = ai_detection.get("fake_probability")
        warning = ai_detection.get("warning")

        if ai_prediction:
            reasons.append(
                f"AI detector prediction: {ai_prediction}."
            )

        if (
            isinstance(fake_probability, (int, float))
            and 0 <= fake_probability <= 1
        ):
            reasons.append(
                f"AI detector fake score: "
                f"{fake_probability * 100:.2f}%. "
                "This is a model output, not a validated probability "
                "that the image is manipulated."
            )

        if warning:
            reasons.append(
                f"AI detector warning: {warning}"
            )

        # Keep the AI score separate from the forensic score.
        # Do not assume the model output is calibrated.

    else:
        reasons.append(
            "AI-based image detection was unavailable."
        )

    # ==========================================
    # LIMIT SCORE
    # ==========================================

    score = round(
        max(0.0, min(score, 100.0)),
        2
    )

    # ==========================================
    # FINAL ASSESSMENT
    # ==========================================

    if ela_status in ("elevated", "high"):
        prediction = "Forensic Review Recommended"
        color = "#FF8C00"

    elif ela_status == "moderate":
        prediction = "Needs Manual Review"
        color = "#DAA520"

    elif ela_status == "low":
        prediction = "No Strong ELA Warning"
        color = "green"

    else:
        prediction = "Insufficient Forensic Evidence"
        color = "#808080"

        # ==========================================
    # PHASE 2: COMBINED FINAL ASSESSMENT
    # ==========================================

    ai_detection = analysis.get("ai_detection", {})

    if not isinstance(ai_detection, dict):
        ai_detection = {}

    ai_prediction = str(
        ai_detection.get("prediction", "")
    ).strip().lower()

    ela = analysis.get("ela", {})

    if not isinstance(ela, dict):
        ela = {}

    ela_status = str(
        ela.get("status", "")
    ).strip().lower()

    copy_move = analysis.get("copy_move", {})

    if not isinstance(copy_move, dict):
        copy_move = {}

    copy_move_matches = copy_move.get("matches", 0)

    if not isinstance(copy_move_matches, (int, float)):
        copy_move_matches = 0

    # ------------------------------------------
    # Rule 1: AI detector is unavailable
    # ------------------------------------------

    if not ai_prediction:

        prediction = "Inconclusive - AI Screening Unavailable"
        color = "#808080"

        reasons.append(
            "The AI detector did not provide a prediction. "
            "The available forensic findings are insufficient "
            "to determine authenticity."
        )

    # ------------------------------------------
    # Rule 2: AI detector flags AI-generated-like
    # ------------------------------------------

    elif ai_prediction == "ai-generated-like":

        prediction = "AI Screening Flag - Manual Review Recommended"
        color = "#FF8C00"

        reasons.append(
            "The AI detector flagged the image as AI-generated-like. "
            "This is a screening result, not proof of AI generation."
        )

        if ela_status in ("moderate", "elevated", "high"):

            reasons.append(
                "The AI screening flag and ELA findings warrant "
                "further examination."
            )

    # ------------------------------------------
    # Rule 3: AI detector returns Real-Looking
    # ------------------------------------------

    elif ai_prediction == "real-looking":

        if ela_status in ("elevated", "high"):

            prediction = "Forensic Review Recommended"
            color = "#FF8C00"

            reasons.append(
                "The AI detector returned Real-Looking, but ELA "
                "reported elevated differences. These results are "
                "not necessarily contradictory and require review."
            )

        elif ela_status == "moderate":

            prediction = "Needs Manual Review"
            color = "#DAA520"

            reasons.append(
                "The AI detector returned Real-Looking, while ELA "
                "reported moderate compression differences. "
                "Manual review is recommended."
            )

        elif ela_status == "low":

            prediction = "No Strong Warning Detected"
            color = "green"

            reasons.append(
                "The AI detector returned Real-Looking and ELA "
                "reported low compression differences. These results "
                "do not establish that the image is authentic."
            )

        else:

            prediction = "Inconclusive - Further Review Recommended"
            color = "#808080"

            reasons.append(
                "The AI detector returned Real-Looking, but the ELA "
                "result is unavailable or unrecognized. "
                "The available evidence is incomplete."
            )

    # ------------------------------------------
    # Rule 4: Unrecognized AI prediction
    # ------------------------------------------

    else:

        prediction = "Inconclusive - Further Review Recommended"
        color = "#808080"

        reasons.append(
            "The AI detector returned an unrecognized prediction. "
            "The system cannot reliably combine the available "
            "results into a more specific assessment."
        )

    # ------------------------------------------
    # Copy-move context
    # ------------------------------------------

    if copy_move_matches > 0:

        reasons.append(
            "The copy-move detector reported potential matching "
            "features. These require examination of the underlying "
            "image evidence and are not, by themselves, proof "
            "of manipulation."
        )

    # ------------------------------------------
    # Assessment limitations
    # ------------------------------------------

    reasons.append(
        "The final assessment summarizes automated screening "
        "results. The AI model output and forensic indicators "
        "are not independently validated proof of authenticity "
        "or manipulation."
    )
    # ==========================================
    # ASSESSMENT LIMITATIONS
    # ==========================================

    reasons.append(
        "The forensic assessment score is a preliminary heuristic, "
        "not a probability of authenticity. The AI screening result "
        "is evaluated separately. Neither result alone can confirm "
        "or rule out image manipulation."
    )

    # ==========================================
    # RETURN RESULT
    # ==========================================

    return {
        "prediction": prediction,
        "integrity_score": score,
        "color": color,
        "reasons": reasons
    }

def calculate_video_score(video_analysis):
    """
    Calculate a provisional video screening estimate
    from the average frame-level fake probability.

    This is not a validated probability of authenticity.
    """

    summary = video_analysis.get("detection_summary", {})

    if not isinstance(summary, dict):
        summary = {}

    average_fake_probability = summary.get(
        "average_fake_probability"
    )

    frames_analyzed = summary.get("frames_analyzed", 0)
    analysis_status = summary.get("analysis_status", "failed")

    # Validate the available frame analysis
    if (
        analysis_status not in ("completed", "partial")
        or not isinstance(frames_analyzed, int)
        or frames_analyzed <= 0
        or not isinstance(average_fake_probability, (int, float))
        or not 0 <= average_fake_probability <= 1
    ):
        return {
            "prediction": "Analysis Incomplete",
            "integrity_score": None,
            "color": "#808080",
            "score_type": "Unavailable",
            "reasons": [
                "No valid frame-level screening result is available.",
                "The system cannot calculate a video screening estimate."
            ]
        }

    fake_percentage = average_fake_probability * 100

    # Provisional inverse model-score estimate
    integrity_score = round(100 - fake_percentage, 2)

    if fake_percentage >= 50:
        prediction = "Potential AI-Generated Content"
        color = "#DC2626"

    elif fake_percentage >= 20:
        prediction = "Inconclusive - Further Review Needed"
        color = "#D97706"

    else:
        prediction = "No Strong AI-Generation Signal Detected"
        color = "#16A34A"

    reasons = [
        f"Average frame-level fake score: {fake_percentage:.2f}%.",
        f"Frames successfully analyzed: {frames_analyzed}.",
        f"Provisional video screening estimate: {integrity_score}/100.",
        (
            "This estimate is derived from the frame-level AI model. "
            "It is not a validated probability of video authenticity."
        )
    ]

    if analysis_status == "partial":
        reasons.append(
            "Some frames could not be analyzed. "
            "Interpret this result with additional caution."
        )

    return {
        "prediction": prediction,
        "integrity_score": integrity_score,
        "color": color,
        "score_type": "Provisional Video Screening Estimate",
        "average_fake_probability": round(
            average_fake_probability, 6
        ),
        "frames_analyzed": frames_analyzed,
        "analysis_status": analysis_status,
        "reasons": reasons
    }