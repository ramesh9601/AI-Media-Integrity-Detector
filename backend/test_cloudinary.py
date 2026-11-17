import cloudinary
import cloudinary.api
import os

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True
)

try:
    result = cloudinary.api.ping()
    print("Cloudinary connection successful!")
    print("Status:", result.get("status"))

except Exception as e:
    print("Cloudinary connection failed!")
    print("Error:", str(e))