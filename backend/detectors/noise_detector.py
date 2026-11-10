import cv2
import os


def detect_noise(image_path):

    image = cv2.imread(image_path)

    if image is None:
        raise ValueError("Unable to read image for noise analysis.")

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Calculate Laplacian noise
    noise = cv2.Laplacian(gray, cv2.CV_64F)

    # Calculate noise variation
    noise_variance = float(noise.var())

    # Convert for visualization
    noise_image = cv2.convertScaleAbs(noise)

    # Create reports directory
    output_folder = "reports"
    os.makedirs(output_folder, exist_ok=True)

    output_name = "NOISE_" + os.path.basename(image_path)

    output_path = os.path.join(
        output_folder,
        output_name
    )

    cv2.imwrite(output_path, noise_image)

    # Basic noise assessment
    if noise_variance < 100:
        status = "Low"
        score = 90
        details = "Low noise variation detected."

    elif noise_variance < 500:
        status = "Moderate"
        score = 65
        details = "Moderate noise variation detected."

    elif noise_variance < 1500:
        status = "Elevated"
        score = 40
        details = "Elevated noise variation detected."

    else:
        status = "High"
        score = 20
        details = "High noise variation detected."

    return {
        "report": output_path,
        "noise_variance": round(noise_variance, 2),
        "score": score,
        "status": status,
        "details": details
    }