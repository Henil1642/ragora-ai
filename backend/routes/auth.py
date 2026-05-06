"""
Authentication routes
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta

from database.db import get_db
from database.models import User
from schemas.auth import UserCreate, UserLogin, UserResponse, TokenResponse
from services.auth_service import AuthService
from utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)
auth_service = AuthService()


@router.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user
    """
    # Check if user exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        logger.warning(f"Registration failed: Email {user_data.email} already exists")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Create new user
    user = auth_service.create_user(user_data, db)
    logger.info(f"User registered: {user.email}")

    return user


@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """
    Login user and return JWT token
    """
    user = db.query(User).filter(User.email == credentials.email).first()

    if not user or not auth_service.verify_password(
        credentials.password, user.hashed_password
    ):
        logger.warning(f"Login failed: Invalid credentials for {credentials.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    # Generate token
    access_token = auth_service.create_access_token(user.id)
    logger.info(f"User logged in: {user.email}")

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=1800,
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    current_user: User = Depends(auth_service.get_current_user),
):
    """
    Get current user profile
    """
    return current_user