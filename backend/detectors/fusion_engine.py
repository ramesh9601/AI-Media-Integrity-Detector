def calculate_score(analysis):

    score = 100
    reasons = []

    # -----------------------------
    # EXIF Metadata Check
    # -----------------------------
    exif = analysis.get("exif", {})

    if len(exif) == 0:
        score -= 15
        reasons.append("No EXIF metadata found.")

    # -----------------------------
    # Image Resolution Check
    # -----------------------------
    width = analysis.get("width", 0)
    height = analysis.get("height", 0)

    if width < 500 or height < 500:
        score -= 10
        reasons.append("Low image resolution.")

    # -----------------------------
    # File Size Check
    # -----------------------------
    file_size = analysis.get("file_size_bytes", 0)

    if file_size < 100000:
        score -= 10
        reasons.append("Very small image size.")

    # -----------------------------
    # Ensure score stays within 0-100
    # -----------------------------
    score = max(0, min(score, 100))

    # -----------------------------
    # Prediction Levels
    # -----------------------------
    if score >= 95:
        prediction = "Authentic"
        color = "green"

    elif score >= 85:
        prediction = "Probably Authentic"
        color = "green"

    elif score >= 70:
        prediction = "Needs Manual Review"
        color = "gold"

    elif score >= 50:
        prediction = "Suspicious"
        color = "orange"

    elif score >= 30:
        prediction = "High Risk"
        color = "red"

    elif score >= 10:
        prediction = "Likely Deepfake"
        color = "darkred"

    else:
        prediction = "Confirmed Manipulation"
        color = "black"

    # -----------------------------
    # If nothing suspicious
    # -----------------------------
    if not reasons:
        reasons.append("No suspicious indicators detected.")

    # -----------------------------
    # Return Result
    # -----------------------------
    return {
        "prediction": prediction,
        "confidence": score,
        "color": color,
        "reasons": reasons
    }