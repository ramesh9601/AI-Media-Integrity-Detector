
import sqlite3
import os

DB_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "media_detector.db"
)

connection = sqlite3.connect(DB_PATH)
cursor = connection.cursor()

cursor.execute("PRAGMA table_info(uploads)")
existing_columns = {
    column[1] for column in cursor.fetchall()
}

new_columns = {
    "integrity_score": "REAL",
    "prediction": "TEXT",
    "report_path": "TEXT",
}

for column_name, column_type in new_columns.items():
    if column_name not in existing_columns:
        cursor.execute(
            f"ALTER TABLE uploads ADD COLUMN "
            f"{column_name} {column_type}"
        )
        print(f"Added column: {column_name}")
    else:
        print(f"Already exists: {column_name}")

connection.commit()
connection.close()

print("Database migration completed.")
