import cv2
import os


def detect_copy_move(image_path):

    image = cv2.imread(image_path)

    if image is None:
        raise ValueError("Unable to read image for copy-move analysis.")

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Detect ORB features
    orb = cv2.ORB_create(
        nfeatures=1000
    )

    keypoints, descriptors = orb.detectAndCompute(
        gray,
        None
    )

    output = image.copy()

    # Default result
    suspicious_matches = 0

    if descriptors is not None and len(descriptors) > 1:

        # FLANN-based matching
        matcher = cv2.BFMatcher(
            cv2.NORM_HAMMING,
            crossCheck=True
        )

        matches = matcher.match(
            descriptors,
            descriptors
        )

        # Remove self-matches
        valid_matches = [
            match
            for match in matches
            if match.queryIdx != match.trainIdx
        ]

        # Sort by distance
        valid_matches = sorted(
            valid_matches,
            key=lambda match: match.distance
        )

        # Keep only relatively strong matches
        good_matches = [
            match
            for match in valid_matches
            if match.distance < 35
        ]

        suspicious_matches = len(good_matches)

        # Draw detected feature points
        output = cv2.drawKeypoints(
            output,
            keypoints,
            None,
            color=(0, 255, 0)
        )

    # Create reports directory
    output_folder = "reports"
    os.makedirs(output_folder, exist_ok=True)

    output_name = "COPYMOVE_" + os.path.basename(image_path)

    output_path = os.path.join(
        output_folder,
        output_name
    )

    cv2.imwrite(
        output_path,
        output
    )

    # Basic assessment
    if suspicious_matches == 0:
        status = "Low"
        score = 90
        details = "No strong duplicate feature matches detected."

    elif suspicious_matches < 5:
        status = "Moderate"
        score = 70
        details = "A small number of similar feature matches detected."

    elif suspicious_matches < 15:
        status = "Elevated"
        score = 45
        details = "Several similar feature matches detected."

    else:
        status = "High"
        score = 20
        details = "A high number of similar feature matches detected."

    return {
        "report": output_path,
        "matches": suspicious_matches,
        "score": score,
        "status": status,
        "details": details
    }