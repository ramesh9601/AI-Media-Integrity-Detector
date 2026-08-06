from PIL import Image
from PIL.ExifTags import TAGS


def extract_exif(image_path):

    exif_data = {}

    try:

        image = Image.open(image_path)

        exif = image.getexif()

        if exif:

            for tag_id, value in exif.items():

                tag = TAGS.get(tag_id, tag_id)

                exif_data[str(tag)] = str(value)

    except Exception as e:

        exif_data["error"] = str(e)

    return exif_data