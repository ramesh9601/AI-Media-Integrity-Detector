import cv2
import os


def detect_copy_move(image_path):

    image = cv2.imread(image_path)

    if image is None:
        raise ValueError(
            "Unable to read image for copy-move analysis."
        )

    gray = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY
    )

    # Detect ORB features
    orb = cv2.ORB_create(
        nfeatures=1500
    )

    keypoints, descriptors = orb.detectAndCompute(
        gray,
        None
    )

    output = image.copy()

    good_matches = []
    inlier_matches = []

    if descriptors is not None and len(descriptors) > 1:

        matcher = cv2.BFMatcher(
            cv2.NORM_HAMMING,
            crossCheck=False
        )

        # Find the two closest matches for each descriptor
        knn_matches = matcher.knnMatch(
            descriptors,
            descriptors,
            k=2
        )

        candidate_matches = []

        height, width = gray.shape

        # Minimum distance between two matched points
        min_spatial_distance = max(
            30,
            min(width, height) * 0.05
        )

        for pair in knn_matches:

            if len(pair) < 2:
                continue

            first, second = pair

            # Remove self-match
            if first.queryIdx == first.trainIdx:
                continue

            # Lowe-style ratio test
            if first.distance >= 0.75 * second.distance:
                continue

            point1 = keypoints[first.queryIdx].pt
            point2 = keypoints[first.trainIdx].pt

            spatial_distance = (
                (point1[0] - point2[0]) ** 2
                +
                (point1[1] - point2[1]) ** 2
            ) ** 0.5

            # A copy-move candidate should occur
            # in a different spatial location.
            if spatial_distance < min_spatial_distance:
                continue

            candidate_matches.append(first)

        good_matches = candidate_matches

        # Geometric verification
        if len(good_matches) >= 4:

            source_points = []
            destination_points = []

            for match in good_matches:

                source_points.append(
                    keypoints[match.queryIdx].pt
                )

                destination_points.append(
                    keypoints[match.trainIdx].pt
                )

            source_points = (
                __import__("numpy")
                .float32(source_points)
                .reshape(-1, 1, 2)
            )

            destination_points = (
                __import__("numpy")
                .float32(destination_points)
                .reshape(-1, 1, 2)
            )

            try:

                matrix, mask = cv2.findHomography(
                    source_points,
                    destination_points,
                    cv2.RANSAC,
                    5.0
                )

                if mask is not None:

                    for match, flag in zip(
                        good_matches,
                        mask.ravel()
                    ):

                        if flag:
                            inlier_matches.append(match)

            except cv2.error:
                inlier_matches = []

    # Number of geometrically consistent matches
    suspicious_matches = len(
        inlier_matches
    )

    # Draw candidate/inlier matches
    if suspicious_matches > 0:

        for match in inlier_matches:

            point1 = tuple(
                map(
                    int,
                    keypoints[match.queryIdx].pt
                )
            )

            point2 = tuple(
                map(
                    int,
                    keypoints[match.trainIdx].pt
                )
            )

            cv2.circle(
                output,
                point1,
                5,
                (0, 255, 0),
                2
            )

            cv2.circle(
                output,
                point2,
                5,
                (0, 255, 0),
                2
            )

            cv2.line(
                output,
                point1,
                point2,
                (0, 255, 0),
                1
            )

    # Create reports directory
    output_folder = "reports"
    os.makedirs(
        output_folder,
        exist_ok=True
    )

    output_name = (
        "COPYMOVE_" +
        os.path.basename(image_path)
    )

    output_path = os.path.join(
        output_folder,
        output_name
    )

    cv2.imwrite(
        output_path,
        output
    )

    # ------------------------------------------
    # Copy-Move Assessment
    # ------------------------------------------

    if suspicious_matches == 0:

        status = "Low"
        score = 90

        details = (
            "No geometrically consistent "
            "duplicate feature matches detected."
        )

    elif suspicious_matches < 5:

        status = "Moderate"
        score = 70

        details = (
            "A small number of geometrically "
            "consistent duplicate features detected."
        )

    elif suspicious_matches < 15:

        status = "Elevated"
        score = 45

        details = (
            "Several geometrically consistent "
            "duplicate features detected."
        )

    else:

        status = "High"
        score = 20

        details = (
            "A high number of geometrically "
            "consistent duplicate features detected."
        )

    return {
        "report": output_path,
        "matches": suspicious_matches,
        "candidate_matches": len(good_matches),
        "score": score,
        "status": status,
        "details": details
    }