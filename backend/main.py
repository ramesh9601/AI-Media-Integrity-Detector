from fastapi import FastAPI

from app.routers import upload, health

from database.database import engine
from database.models import Base

# Create database tables automatically
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI Media Integrity Detector",
    description="AI-Powered Deepfake and Media Integrity Detection API",
    version="2.0.0"
)

app.include_router(health.router)
app.include_router(upload.router)