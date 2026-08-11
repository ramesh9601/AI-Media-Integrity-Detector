def calculate_score(analysis):

    score = 100
    reasons = []

    # ==========================================
    # EXIF METADATA
    # ==========================================

    exif = analysis.get("exif", {})

    if len(exif) == 0:
        score -= 10
        reasons.append("No EXIF metadata found.")
    else:
        reasons.append("EXIF metadata is available for the image.")

    # ==========================================
    # IMAGE RESOLUTION
    # ==========================================

    width = analysis.get("width", 0)
    height = analysis.get("height", 0)

    if width < 500 or height < 500:
        score -= 5
        reasons.append("Low image resolution.")

    # ==========================================
    # FILE SIZE
    # ==========================================

    file_size = analysis.get("file_size_bytes", 0)

    if file_size < 100000:
        score -= 5
        reasons.append("Very small image size.")

    # ==========================================
    # ELA ANALYSIS
    # ==========================================

    ela = analysis.get("ela", {})

    if ela:

        ela_score = ela.get("score", 90)
        ela_status = ela.get("status", "Unknown")
        ela_details = ela.get("details")

        # Convert detector score into penalty
        ela_penalty = (90 - ela_score) * 0.25

        score -= ela_penalty

        if ela_details:
            reasons.append(
                f"ELA: {ela_details}"
            )

    # ==========================================
    # NOISE ANALYSIS
    # ==========================================

    noise = analysis.get("noise", {})

    if noise:

        noise_score = noise.get("score", 90)
        noise_status = noise.get("status", "Unknown")
        noise_details = noise.get("details")

        noise_penalty = (90 - noise_score) * 0.20

        score -= noise_penalty

        if noise_details:
            reasons.append(
                f"Noise analysis: {noise_details}"
            )

    # ==========================================
    # COPY-MOVE ANALYSIS
    # ==========================================

    copy_move = analysis.get("copy_move", {})

    if copy_move:

        copy_move_score = copy_move.get("score", 90)
        copy_move_status = copy_move.get(
            "status",
            "Unknown"
        )

        copy_move_details = copy_move.get(
            "details"
        )

        copy_move_penalty = (
            (90 - copy_move_score) * 0.35
        )

        score -= copy_move_penalty

        if copy_move_details:
            reasons.append(
                f"Copy-move analysis: "
                f"{copy_move_details}"
            )

    # ==========================================
    # LIMIT SCORE
    # ==========================================

    score = round(
        max(0, min(score, 100)),
        2
    )

    # ==========================================
    # CLASSIFICATION
    # ==========================================

    if score >= 95:

        prediction = "Authentic"
        color = "green"

    elif score >= 85:

        prediction = "Probably Authentic"
        color = "#2E8B57"

    elif score >= 70:

        prediction = "Needs Manual Review"
        color = "#DAA520"

    elif score >= 50:

        prediction = "Suspicious"
        color = "#FF8C00"

    elif score >= 30:

        prediction = "High Risk"
        color = "red"

    elif score >= 10:

        prediction = "Likely Deepfake"
        color = "#8B0000"

    else:

        prediction = "Confirmed Manipulation"
        color = "black"

    # ==========================================
    # NO SUSPICIOUS INDICATORS
    # ==========================================

    if not reasons:

        reasons.append(
            "No significant suspicious indicators "
            "were detected by the available analyses."
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