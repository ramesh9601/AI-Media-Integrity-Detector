
import os
import sqlite3

DB_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "media_detector.db"
)

connection = sqlite3.connect(DB_PATH)
cursor = connection.cursor()

try:
    cursor.execute("PRAGMA table_info(uploads)")
    columns = {column[1] for column in cursor.fetchall()}

    if "user_id" not in columns:
        cursor.execute(
            "ALTER TABLE uploads ADD COLUMN user_id INTEGER "
            "REFERENCES users(id)"
        )
        print("Added user_id column to uploads table.")
    else:
        print("user_id column already exists.")

    cursor.execute(
        "CREATE INDEX IF NOT EXISTS ix_uploads_user_id "
        "ON uploads(user_id)"
    )

    connection.commit()
    print("Database migration completed successfully.")

except Exception:
    connection.rollback()
    raise

finally:
    connection.close()
