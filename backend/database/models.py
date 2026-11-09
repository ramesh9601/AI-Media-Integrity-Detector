
from sqlalchemy import Column, Integer, String, Float, ForeignKey
from database.database import Base


class Upload(Base):
    __tablename__ = "uploads"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    original_filename = Column(String)
    saved_filename = Column(String)
    file_type = Column(String)
    status = Column(String)

    integrity_score = Column(Float, nullable=True)
    prediction = Column(String, nullable=True)
    report_path = Column(String, nullable=True)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
