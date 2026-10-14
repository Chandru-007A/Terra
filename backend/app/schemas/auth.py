"""
Pydantic schemas for authentication and user profiles.
"""

from typing import Optional
from pydantic import BaseModel, EmailStr


class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str
    village: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    name: Optional[str] = None
    village: Optional[str] = None
    district: Optional[str] = None
    farmSizeAcres: Optional[float] = None
    soilType: Optional[str] = None
    language: Optional[str] = None


class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    village: Optional[str] = None
    district: Optional[str] = None
    farmSizeAcres: Optional[float] = None
    soilType: Optional[str] = None
    language: Optional[str] = None
    createdAt: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
