from PIL import Image, ImageChops, ImageEnhance
import os


def perform_ela(image_path):

    # Open original image
    original = Image.open(image_path).convert("RGB")

    # Temporary compressed image
    temp_path = image_path + ".temp.jpg"

    # Save with JPEG quality 90
    original.save(temp_path, "JPEG", quality=90)

    # Open compressed image
    compressed = Image.open(temp_path)

    # Difference between original and compressed
    diff = ImageChops.difference(original, compressed)

    # Get maximum pixel difference
    extrema = diff.getextrema()
    max_diff = max([e[1] for e in extrema])

    if max_diff == 0:
        max_diff = 1

    # Enhance brightness
    scale = 255.0 / max_diff
    ela_image = ImageEnhance.Brightness(diff).enhance(scale)

    # Save ELA image
    ela_folder = "reports"

    os.makedirs(ela_folder, exist_ok=True)

    ela_filename = os.path.basename(image_path)

    ela_output = os.path.join(
        ela_folder,
        "ELA_" + ela_filename
    )

    ela_image.save(ela_output)

    # Delete temporary file
    os.remove(temp_path)

    return ela_output