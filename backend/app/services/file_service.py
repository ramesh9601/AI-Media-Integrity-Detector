import os
import shutil
import uuid

from app.config import UPLOAD_FOLDER


def save_file(file):
    extension = os.path.splitext(file.filename)[1]

    unique_name = f"{uuid.uuid4()}{extension}"

    file_path = os.path.join(UPLOAD_FOLDER, unique_name)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return unique_name