import os
import shutil
import uuid
from PIL import Image

from app.config import UPLOAD_FOLDER, ALLOWED_EXTENSIONS

MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB

def validate_video_signature(file_path, extension):
    with open(file_path, "rb") as video:
        header = video.read(32)

    if extension == ".mp4":
        valid = (
            len(header) >= 12
            and header[4:8] == b"ftyp"
        )

    elif extension == ".mov":
        valid = (
            len(header) >= 12
            and header[4:8] == b"ftyp"
        )

    elif extension == ".avi":
        valid = (
            len(header) >= 12
            and header[:4] == b"RIFF"
            and header[8:12] == b"AVI "
        )

    else:
        valid = False

    if not valid:
        raise ValueError(
            "Uploaded file does not contain a valid video signature."
        )
        
def validate_audio_signature(file_path, extension):
    with open(file_path, "rb") as audio:
        header = audio.read(12)

    if extension == ".wav":
        valid = (
            len(header) >= 12
            and header[:4] == b"RIFF"
            and header[8:12] == b"WAVE"
        )

    elif extension == ".mp3":
        valid = (
            header.startswith(b"ID3")
            or (
                len(header) >= 2
                and header[0] == 0xFF
                and (header[1] & 0xE0) == 0xE0
            )
        )

    else:
        valid = False

    if not valid:
        raise ValueError(
            "Uploaded file does not contain a valid audio signature."
        )

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
        # Save uploaded file in chunks with size validation
        total_size = 0

        with open(file_path, "wb") as buffer:
            while True:
                chunk = file.file.read(1024 * 1024)

                if not chunk:
                    break

                total_size += len(chunk)

                if total_size > MAX_FILE_SIZE:
                    raise ValueError(
                        "File size exceeds the 100 MB limit."
                    )

                buffer.write(chunk)

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
                    actual_format = image.format
                    image.verify()

                # Verify actual image format matches extension
                expected_formats = {
                    ".jpg": "JPEG",
                    ".jpeg": "JPEG",
                    ".png": "PNG"
                }

                if actual_format != expected_formats[extension]:
                    raise ValueError(
                        "Image content does not match the file extension."
                    )

                with Image.open(file_path) as image:
                    width, height = image.size

            except ValueError:
                raise

            except Exception:
                raise ValueError(
                    "Uploaded file is not a valid image."
                )

            if width < 100 or height < 100:
                raise ValueError(
                    "Image dimensions are too small. "
                    "Minimum size is 100 x 100 pixels."
                )

        # Validate video file signatures
        if extension in {".mp4", ".mov", ".avi"}:
            validate_video_signature(file_path, extension)

        # Validate audio file signatures
        if extension in {".wav", ".mp3"}:
            validate_audio_signature(file_path, extension)

        return unique_name

    except Exception:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise
