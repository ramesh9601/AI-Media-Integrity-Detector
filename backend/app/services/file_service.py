import os
import shutil
import uuid
from PIL import Image

from app.config import UPLOAD_FOLDER


MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


def save_file(file):

    # Check filename
    if not file.filename:
        raise ValueError("No filename provided.")

    extension = os.path.splitext(
        file.filename
    )[1].lower()

    # Check extension
    allowed_extensions = {
        ".jpg",
        ".jpeg",
        ".png"
    }

    if extension not in allowed_extensions:
        raise ValueError(
            "Unsupported file type."
        )

    # Make sure upload directory exists
    os.makedirs(
        UPLOAD_FOLDER,
        exist_ok=True
    )

    # Generate unique filename
    unique_name = (
        f"{uuid.uuid4()}{extension}"
    )

    file_path = os.path.join(
        UPLOAD_FOLDER,
        unique_name
    )

    # Save file
    with open(
        file_path,
        "wb"
    ) as buffer:

        shutil.copyfileobj(
            file.file,
            buffer
        )

    # Check file size
    file_size = os.path.getsize(
        file_path
    )

    if file_size == 0:

        os.remove(file_path)

        raise ValueError(
            "Uploaded file is empty."
        )

    if file_size > MAX_FILE_SIZE:

        os.remove(file_path)

        raise ValueError(
            "File size exceeds the 10 MB limit."
        )
    # Validate actual image content
    try:
        with Image.open(file_path) as image:
            image.verify()

    except Exception:

        if os.path.exists(file_path):
            os.remove(file_path)

        raise ValueError(
            "Uploaded file is not a valid image."
        )
        # Validate image dimensions
    try:
        with Image.open(file_path) as image:
            width, height = image.size

    except Exception:

        if os.path.exists(file_path):
            os.remove(file_path)

        raise ValueError(
            "Unable to read image dimensions."
        )

    if width < 100 or height < 100:

        if os.path.exists(file_path):
            os.remove(file_path)

        raise ValueError(
            "Image dimensions are too small. "
            "Minimum size is 100 x 100 pixels."
        )
    
    return unique_name