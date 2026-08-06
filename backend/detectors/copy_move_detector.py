import cv2
import os


def detect_copy_move(image_path):

    image = cv2.imread(image_path)

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    orb = cv2.ORB_create(500)

    keypoints, descriptors = orb.detectAndCompute(gray, None)

    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)

    matches = []

    if descriptors is not None:

        matches = bf.match(descriptors, descriptors)

        matches = sorted(matches, key=lambda x: x.distance)

    output = image.copy()

    output = cv2.drawKeypoints(
        output,
        keypoints,
        None,
        color=(0,255,0)
    )

    output_name = "COPYMOVE_" + os.path.basename(image_path)

    output_path = os.path.join("reports", output_name)

    cv2.imwrite(output_path, output)

    return output_path