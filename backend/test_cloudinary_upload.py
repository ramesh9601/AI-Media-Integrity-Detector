import os
from app.services.cloudinary_service import upload_to_cloudinary

# Create a temporary test file
test_file = "cloudinary_test.txt"

with open(test_file, "w") as file:
    file.write("AI Media Integrity Detector - Cloudinary Test")

try:
    result = upload_to_cloudinary(
        file_path=test_file,
        resource_type="raw",
        folder="media_integrity_test"
    )

    print("File uploaded successfully!")
    print("Cloudinary URL:", result["url"])
    print("Public ID:", result["public_id"])

except Exception as e:
    print("Upload failed:", str(e))

finally:
    if os.path.exists(test_file):
        os.remove(test_file)