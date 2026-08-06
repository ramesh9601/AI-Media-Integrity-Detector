from sqlalchemy import Column, Integer, String

from database.database import Base


class Upload(Base):

    __tablename__ = "uploads"

    id = Column(Integer, primary_key=True, index=True)

    original_filename = Column(String)

    saved_filename = Column(String)

    file_type = Column(String)

    status = Column(String)