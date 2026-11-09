
from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status
)

from fastapi.security import (
    HTTPBearer,
    HTTPAuthorizationCredentials
)

from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from database.database import get_db
from database.models import User


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


# Password hashing
password_hash = PasswordHash.recommended()


# JWT configuration
SECRET_KEY = "CHANGE_THIS_TO_A_LONG_RANDOM_SECRET_BEFORE_DEPLOYMENT"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


# Authentication schemes
oauth2_scheme = HTTPBearer()

optional_oauth2_scheme = HTTPBearer(auto_error=False)


# Request models
class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


# Create JWT access token
def create_access_token(user_id: int) -> str:

    expires = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": str(user_id),
        "exp": expires
    }

    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM
    )


# User registration
@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED
)
def register_user(
    data: RegisterRequest,
    db: Session = Depends(get_db)
):

    email = str(data.email).lower()

    if not data.name.strip():
        raise HTTPException(
            status_code=400,
            detail="Name is required"
        )

    if len(data.password) < 8:
        raise HTTPException(
            status_code=400,
            detail="Password must contain at least 8 characters"
        )

    existing_user = db.query(User).filter(
        User.email == email
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=409,
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


# User login
@router.post("/login")
def login_user(
    data: LoginRequest,
    db: Session = Depends(get_db)
):

    email = str(data.email).lower()

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


# Get current logged-in user
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
            algorithms=[ALGORITHM]
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


# Get current user if logged in; otherwise allow guest access
def get_optional_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(
        optional_oauth2_scheme
    ),
    db: Session = Depends(get_db)
):

    # No token means guest user
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
            algorithms=[ALGORITHM]
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
