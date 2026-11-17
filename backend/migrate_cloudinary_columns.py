import os
from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable is missing.")

# Use the pure-Python pg8000 driver
DATABASE_URL = DATABASE_URL.replace(
    "postgresql://",
    "postgresql+pg8000://",
    1
)

DATABASE_URL = DATABASE_URL.replace(
    "postgres://",
    "postgresql+pg8000://",
    1
)

engine = create_engine(
    DATABASE_URL,
    connect_args={"ssl_context": True}
)

try:
    with engine.begin() as connection:

        connection.execute(text("""
            ALTER TABLE uploads
            ADD COLUMN IF NOT EXISTS media_url VARCHAR
        """))

        connection.execute(text("""
            ALTER TABLE uploads
            ADD COLUMN IF NOT EXISTS media_public_id VARCHAR
        """))

        result = connection.execute(text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'uploads'
            ORDER BY ordinal_position
        """))

        print("\nUpdated uploads table:")

        for row in result:
            print(row[0])

    print("\nPostgreSQL migration completed successfully!")

finally:
    engine.dispose()