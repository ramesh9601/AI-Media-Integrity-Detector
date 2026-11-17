import os

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import make_url


# Read database URL
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///media_detector.db"
)

# Configure database driver
url = make_url(DATABASE_URL)

connect_args = {}

if url.get_backend_name() == "postgresql":

    # Use pg8000 for PostgreSQL
    url = url.set(drivername="postgresql+pg8000")

    connect_args = {
        "ssl_context": True
    }

elif url.get_backend_name() == "sqlite":

    connect_args = {
        "check_same_thread": False
    }

DATABASE_URL = url


# Create database engine
engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True
)


try:
    with engine.begin() as connection:

        # Check existing columns
        inspector = inspect(connection)

        columns = [
            column["name"]
            for column in inspector.get_columns("uploads")
        ]

        if "report_public_id" not in columns:

            connection.execute(text("""
                ALTER TABLE uploads
                ADD COLUMN report_public_id VARCHAR
            """))

            print("report_public_id column added successfully.")

        else:
            print("report_public_id column already exists.")

        # Verify migration
        inspector = inspect(connection)

        print("\nUpdated uploads table:")

        for column in inspector.get_columns("uploads"):
            print(column["name"])

    print("\nDatabase migration completed successfully!")

finally:
    engine.dispose()