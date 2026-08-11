from PIL import Image, ImageChops, ImageEnhance
import os


def perform_ela(image_path):

    # Open original image
    original = Image.open(image_path).convert("RGB")

    # Temporary JPEG file
    temp_path = image_path + ".temp.jpg"

    # Save compressed copy
    original.save(temp_path, "JPEG", quality=90)

    # Open compressed image
    compressed = Image.open(temp_path).convert("RGB")

    # Calculate difference
    diff = ImageChops.difference(original, compressed)

    # Find maximum pixel difference
    extrema = diff.getextrema()
    max_diff = max(e[1] for e in extrema)

    if max_diff == 0:
        max_diff = 1

    # Enhance ELA visualization
    scale = 255.0 / max_diff

    ela_image = ImageEnhance.Brightness(diff).enhance(scale)

    # Create reports directory
    ela_folder = "reports"
    os.makedirs(ela_folder, exist_ok=True)

    # Output filename
    original_filename = os.path.basename(image_path)

    ela_filename = "ELA_" + original_filename
    ela_output = os.path.join(
        ela_folder,
        ela_filename
    )

    # Save ELA image
    ela_image.save(ela_output)

    # Remove temporary file
    if os.path.exists(temp_path):
        os.remove(temp_path)

    # Basic ELA assessment
    if max_diff <= 10:
        status = "Low"
        score = 90
        details = "Low compression difference detected."

    elif max_diff <= 30:
        status = "Moderate"
        score = 65
        details = "Moderate compression differences detected."

    elif max_diff <= 60:
        status = "Elevated"
        score = 40
        details = "Elevated compression differences detected."

    else:
        status = "High"
        score = 20
        details = "High compression differences detected."

    return {
        "report": ela_output,
        "max_difference": max_diff,
        "score": score,
        "status": status,
        "details": details
    }