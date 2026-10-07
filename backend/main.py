from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.routers import upload, health
from database.database import engine
from database.models import Base

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI Media Integrity Detector",
    description="AI-Powered Deepfake and Media Integrity Detection API",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.mount(
    "/reports",
    StaticFiles(directory="reports"),
    name="reports"
)

app.include_router(health.router)
app.include_router(upload.router)