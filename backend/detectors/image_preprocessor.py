import cv2
import os


def analyze_image(image_path):

    image = cv2.imread(image_path)

    if image is None:
        return {
            "status": "Invalid",
            "error": "Image could not be loaded."
        }

    height, width, channels = image.shape

    file_size = os.path.getsize(
        image_path
    )

    # ------------------------------------------
    # Aspect Ratio
    # ------------------------------------------

    aspect_ratio = round(
        width / height,
        3
    ) if height > 0 else 0

    # ------------------------------------------
    # Image Type
    # ------------------------------------------

    if channels == 1:
        image_type = "Grayscale"

    elif channels == 3:
        image_type = "Color"

    elif channels == 4:
        image_type = "Color with Alpha"

    else:
        image_type = "Unknown"

    # ------------------------------------------
    # Resolution Assessment
    # ------------------------------------------

    if width < 100 or height < 100:

        resolution_status = "Very Low"

    elif width < 500 or height < 500:

        resolution_status = "Low"

    elif width < 1000 or height < 1000:

        resolution_status = "Moderate"

    else:

        resolution_status = "Good"

    # ------------------------------------------
    # Return Analysis
    # ------------------------------------------

    return {
        "status": "Valid",
        "width": width,
        "height": height,
        "channels": channels,
        "image_type": image_type,
        "aspect_ratio": aspect_ratio,
        "resolution_status": resolution_status,
        "file_size_bytes": file_size
    }