import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.routers import upload, health, auth
from database.database import engine
from database.models import Base

# Create database tables
Base.metadata.create_all(bind=engine)

# Create reports directory if it does not exist
os.makedirs("reports", exist_ok=True)

app = FastAPI(
    title="AI Media Integrity Detector",
    description="AI-Powered Deepfake and Media Integrity Detection API",
    version="2.0.0"
)

# Frontend URLs
frontend_url = os.getenv("FRONTEND_URL")

allowed_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173"
]

if frontend_url:
    allowed_origins.append(frontend_url.rstrip("/"))

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve generated PDF reports
app.mount(
    "/reports",
    StaticFiles(directory="reports"),
    name="reports"
)

# Register API routers
app.include_router(health.router)
app.include_router(upload.router)
app.include_router(auth.router)
