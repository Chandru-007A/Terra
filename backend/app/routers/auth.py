"""
Authentication router for farmer registration, login, and profile management.
"""

from datetime import datetime, timezone
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models.user import User
from backend.app.schemas.auth import (
    UserRegister,
    UserLogin,
    UserUpdate,
    UserResponse,
    TokenResponse,
)
from backend.app.utils.security import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user_id,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


def user_to_response(u: User) -> UserResponse:
    created = u.created_at.isoformat() if u.created_at else datetime.now(timezone.utc).isoformat()
    return UserResponse(
        id=u.id,
        name=u.name,
        email=u.email,
        village=u.village,
        district=u.district,
        farmSizeAcres=u.farm_size_acres,
        soilType=u.soil_type,
        language=u.language,
        createdAt=created,
    )


@router.post("/register", response_model=TokenResponse)
def register(payload: UserRegister, db: Session = Depends(get_db)):
    """Register a new farmer account."""
    existing = db.query(User).filter(User.email.ilike(payload.email)).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    user_id = f"user-{uuid.uuid4().hex[:12]}"
    pwd_hash = hash_password(payload.password)

    new_user = User(
        id=user_id,
        name=payload.name.strip(),
        email=payload.email.lower().strip(),
        password_hash=pwd_hash,
        village=payload.village.strip() if payload.village else None,
        district="Maharashtra",
        farm_size_acres=10.0,
        soil_type="Black cotton soil",
        language="English",
        created_at=datetime.now(timezone.utc)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    token = create_access_token({"sub": new_user.id, "email": new_user.email})
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=user_to_response(new_user)
    )


@router.post("/login", response_model=TokenResponse)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    """Authenticate with email and password, returning a JWT token."""
    user = db.query(User).filter(User.email.ilike(payload.email)).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email or password is wrong"
        )

    token = create_access_token({"sub": user.id, "email": user.email})
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=user_to_response(user)
    )


@router.get("/me", response_model=UserResponse)
def get_me(
    user_id: Optional[str] = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Retrieve current authenticated user profile. Requires a valid Bearer token."""
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found"
        )
    return user_to_response(user)


@router.patch("/me", response_model=UserResponse)
def update_profile(
    patch: UserUpdate,
    user_id: Optional[str] = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Update farmer profile settings. Requires a valid Bearer token."""
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    if patch.name is not None:
        user.name = patch.name
    if patch.village is not None:
        user.village = patch.village
    if patch.district is not None:
        user.district = patch.district
    if patch.farmSizeAcres is not None:
        user.farm_size_acres = patch.farmSizeAcres
    if patch.soilType is not None:
        user.soil_type = patch.soilType
    if patch.language is not None:
        user.language = patch.language

    db.commit()
    db.refresh(user)
    return user_to_response(user)
