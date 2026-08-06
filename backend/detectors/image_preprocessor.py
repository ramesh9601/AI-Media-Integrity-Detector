import cv2
import os


def analyze_image(image_path):

    image = cv2.imread(image_path)

    if image is None:
        return {
            "error": "Image could not be loaded."
        }

    height, width, channels = image.shape

    file_size = os.path.getsize(image_path)

    return {
        "width": width,
        "height": height,
        "channels": channels,
        "file_size_bytes": file_size
    }