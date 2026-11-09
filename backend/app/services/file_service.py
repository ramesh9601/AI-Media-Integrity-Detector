
import os
import shutil
import uuid
from PIL import Image

from app.config import UPLOAD_FOLDER, ALLOWED_EXTENSIONS

MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB


def save_file(file):
    # Check filename
    if not file.filename:
        raise ValueError("No filename provided.")

    extension = os.path.splitext(file.filename)[1].lower()

    # Check extension
    if extension not in ALLOWED_EXTENSIONS:
        raise ValueError("Unsupported file type.")

    # Create upload directory
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    # Generate unique filename
    unique_name = f"{uuid.uuid4()}{extension}"
    file_path = os.path.join(UPLOAD_FOLDER, unique_name)

    try:
        # Save uploaded file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Check file size
        file_size = os.path.getsize(file_path)

        if file_size == 0:
            raise ValueError("Uploaded file is empty.")

        if file_size > MAX_FILE_SIZE:
            raise ValueError("File size exceeds the 100 MB limit.")

        # Validate image content only for image files
        if extension in {".jpg", ".jpeg", ".png"}:
            try:
                with Image.open(file_path) as image:
                    image.verify()

                with Image.open(file_path) as image:
                    width, height = image.size

            except Exception:
                raise ValueError("Uploaded file is not a valid image.")

            if width < 100 or height < 100:
                raise ValueError(
                    "Image dimensions are too small. "
                    "Minimum size is 100 x 100 pixels."
                )

        # Video and audio files are not image-validated
        return unique_name

    except Exception:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise
