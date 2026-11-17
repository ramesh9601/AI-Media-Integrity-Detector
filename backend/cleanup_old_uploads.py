import argparse
from pathlib import Path
from datetime import datetime, timedelta
from app.config import UPLOAD_FOLDER

# Keep local uploads for 30 days
RETENTION_DAYS = 30

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = Path(UPLOAD_FOLDER)

if not UPLOAD_DIR.is_absolute():
    UPLOAD_DIR = BASE_DIR / UPLOAD_DIR

UPLOAD_DIR = UPLOAD_DIR.resolve()


def cleanup_old_uploads(delete=False):

    if not UPLOAD_DIR.exists():
        print("Upload folder does not exist.")
        return

    cutoff_time = datetime.now() - timedelta(
        days=RETENTION_DAYS
    )

    old_files = []

    for file_path in UPLOAD_DIR.iterdir():

        if not file_path.is_file() or file_path.is_symlink():
            continue

        modified_time = datetime.fromtimestamp(
            file_path.stat().st_mtime
        )

        if modified_time < cutoff_time:
            old_files.append(file_path)

    if not old_files:
        print("No old files found.")
        return

    print(f"Found {len(old_files)} old files.")

    for file_path in old_files:

        if delete:
            file_path.unlink()
            print(f"Deleted: {file_path.name}")

        else:
            print(f"Would delete: {file_path.name}")

    if not delete:
        print("\nDry run completed. No files were deleted.")
        print("Use --delete to perform cleanup.")


if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--delete",
        action="store_true",
        help="Actually delete old files"
    )

    args = parser.parse_args()

    cleanup_old_uploads(delete=args.delete)