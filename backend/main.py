import os

from fastapi import FastAPI, Request
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.limiter import limiter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.routers import upload, health, auth
from database.database import engine
from database.models import Base
from fastapi.middleware.trustedhost import TrustedHostMiddleware

# Create database tables
Base.metadata.create_all(bind=engine)

# Create reports directory if it does not exist
os.makedirs("reports", exist_ok=True)

# Configure API rate limiter


app = FastAPI(
    title="AI Media Integrity Detector",
    description="AI-Powered Deepfake and Media Integrity Detection API",
    version="2.0.0"
)
# Security response headers
@app.middleware("http")
async def add_security_headers(request: Request, call_next):

    response = await call_next(request)

    # Prevent MIME-type sniffing
    response.headers["X-Content-Type-Options"] = "nosniff"

    # Prevent clickjacking
    response.headers["X-Frame-Options"] = "DENY"

    # Control referrer information
    response.headers["Referrer-Policy"] = (
        "strict-origin-when-cross-origin"
    )

    # Restrict unnecessary browser permissions
    response.headers["Permissions-Policy"] = (
        "camera=(), microphone=(), geolocation=()"
    )

    # Enable HTTPS protection
    response.headers["Strict-Transport-Security"] = (
        "max-age=31536000"
    )

    return response
# Trusted host configuration
allowed_hosts = [
    "127.0.0.1",
    "localhost",
    "ai-media-integrity-detector.onrender.com"
]

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=allowed_hosts
)

# Register rate limiter
app.state.limiter = limiter

app.add_exception_handler(
    RateLimitExceeded,
    _rate_limit_exceeded_handler
)

# Frontend URLs
frontend_url = os.getenv("FRONTEND_URL")

allowed_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173"
]

if frontend_url:
    allowed_origins.append(frontend_url.rstrip("/"))

# Secure CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=[
        "GET",
        "POST",
        "OPTIONS"
    ],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "Accept"
    ],
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
