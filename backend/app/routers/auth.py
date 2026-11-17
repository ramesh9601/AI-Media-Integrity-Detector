
from datetime import datetime, timedelta, timezone
import logging
import os

import cloudinary.utils
import jwt
import requests

from pwdlib import PasswordHash

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    status
)

from fastapi.responses import Response

from fastapi.security import (
    HTTPBearer,
    HTTPAuthorizationCredentials
)

from pydantic import BaseModel, EmailStr, Field, field_validator
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from database.database import get_db
from database.models import User, Upload
from app.limiter import limiter


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


# ------------------------------------------
# PASSWORD HASHING
# ------------------------------------------

password_hash = PasswordHash.recommended()


# ------------------------------------------
# JWT CONFIGURATION
# ------------------------------------------

SECRET_KEY = os.getenv("SECRET_KEY")

if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY environment variable is not configured")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
JWT_ISSUER = "AI-Media-Integrity-Detector"


# ------------------------------------------
# AUTHENTICATION SCHEMES
# ------------------------------------------

oauth2_scheme = HTTPBearer()

optional_oauth2_scheme = HTTPBearer(auto_error=False)


# ------------------------------------------
# REQUEST MODELS
# ------------------------------------------

class RegisterRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value):
        value = value.strip()

        if not value:
            raise ValueError("Name is required")

        return value


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


# ------------------------------------------
# CREATE JWT ACCESS TOKEN
# ------------------------------------------

def create_access_token(user_id: int) -> str:

    now = datetime.now(timezone.utc)

    expires = now + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": expires,
        "iss": JWT_ISSUER
    }

    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM
    )


# ------------------------------------------
# USER REGISTRATION
# ------------------------------------------

@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED
)
@limiter.limit("5/minute")
def register_user(
    request: Request,
    data: RegisterRequest,
    db: Session = Depends(get_db)
):

    email = str(data.email).lower()

    try:
        existing_user = db.query(User).filter(
            User.email == email
        ).first()

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email is already registered"
            )

        user = User(
            name=data.name.strip(),
            email=email,
            hashed_password=password_hash.hash(data.password)
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        return {
            "success": True,
            "message": "Registration successful",
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email
            }
        }

    except HTTPException:
        db.rollback()
        raise

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered"
        )

    except SQLAlchemyError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error during registration"
        )


# ------------------------------------------
# USER LOGIN
# ------------------------------------------

@router.post("/login")
@limiter.limit("5/minute")
def login_user(
    request: Request,
    data: LoginRequest,
    db: Session = Depends(get_db)
):

    email = str(data.email).lower()

    try:
        user = db.query(User).filter(
            User.email == email
        ).first()

        if not user or not password_hash.verify(
            data.password,
            user.hashed_password
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )

        token = create_access_token(user.id)

        return {
            "success": True,
            "message": "Login successful",
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email
            }
        }

    except HTTPException:
        raise

    except SQLAlchemyError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error during login"
        )


# ------------------------------------------
# GET CURRENT LOGGED-IN USER
# ------------------------------------------

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):

    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired login token",
        headers={"WWW-Authenticate": "Bearer"}
    )

    try:
        token = credentials.credentials

        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            issuer=JWT_ISSUER,
            options={
                "require": ["sub", "iat", "exp", "iss"]
            }
        )

        user_id = int(payload.get("sub", ""))

    except (jwt.InvalidTokenError, ValueError, TypeError):
        raise credentials_error

    user = db.query(User).filter(
        User.id == user_id
    ).first()

    if user is None:
        raise credentials_error

    return user


# ------------------------------------------
# OPTIONAL USER AUTHENTICATION
# ------------------------------------------

def get_optional_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(
        optional_oauth2_scheme
    ),
    db: Session = Depends(get_db)
):

    if credentials is None:
        return None

    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired login token",
        headers={"WWW-Authenticate": "Bearer"}
    )

    try:
        token = credentials.credentials

        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            issuer=JWT_ISSUER,
            options={
                "require": ["sub", "iat", "exp", "iss"]
            }
        )

        user_id = int(payload.get("sub", ""))

    except (jwt.InvalidTokenError, ValueError, TypeError):
        raise credentials_error

    user = db.query(User).filter(
        User.id == user_id
    ).first()

    if user is None:
        raise credentials_error

    return user


# ------------------------------------------
# SECURE PDF REPORT DOWNLOAD
# ------------------------------------------

@router.get("/reports/download/{upload_id}")
def download_pdf_report(
    upload_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    # Find report belonging to logged-in user.
    upload = (
        db.query(Upload)
        .filter(
            Upload.id == upload_id,
            Upload.user_id == current_user.id
        )
        .first()
    )

    if upload is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found."
        )

    if not upload.report_public_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PDF report is unavailable."
        )

    # Generate five-minute signed Cloudinary URL.
    expiry_timestamp = int(
        (
            datetime.now(timezone.utc)
            + timedelta(minutes=5)
        ).timestamp()
    )

    try:

        download_url = cloudinary.utils.private_download_url(
            upload.report_public_id,
            "pdf",
            resource_type="raw",
            type="private",
            expires_at=expiry_timestamp,
            attachment=False
        )

        # Retrieve PDF from Cloudinary.
        pdf_response = requests.get(
            download_url,
            timeout=30
        )

        pdf_response.raise_for_status()

        # Validate that the response contains a PDF.
        if not pdf_response.content.startswith(b"%PDF-"):
            raise ValueError("Cloudinary did not return a valid PDF.")

        # Return PDF directly to the browser.
        return Response(
            content=pdf_response.content,
            media_type="application/pdf",
            headers={
                "Content-Disposition": (
                    f'inline; filename="report_{upload.id}.pdf"'
                ),
                "Cache-Control": "private, no-store",
                "X-Content-Type-Options": "nosniff"
            }
        )

    except requests.RequestException:
        logger.exception("Cloudinary PDF retrieval failed")

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unable to retrieve PDF from cloud storage."
        )

    except Exception:
        logger.exception("PDF report generation failed")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to open PDF report."
        )
