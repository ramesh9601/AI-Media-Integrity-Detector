import os
import cloudinary
import cloudinary.uploader


cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True
)


def upload_to_cloudinary(
    file_path,
    resource_type,
    folder,
    delivery_type="upload"
):

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    result = cloudinary.uploader.upload(
        file_path,
        resource_type=resource_type,
        folder=folder,
        type=delivery_type
    )

    return {
        "url": result.get("secure_url"),
        "public_id": result.get("public_id")
    }