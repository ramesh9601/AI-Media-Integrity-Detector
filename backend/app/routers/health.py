from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def root():
    return {
        "message": "Welcome to AI Media Integrity Detector",
        "status": "Running Successfully"
    }


@router.get("/health")
def health():
    return {
        "status": "healthy",
        "backend": "FastAPI"
    }