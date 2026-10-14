"""
Security utilities: Password hashing (PBKDF2-HMAC-SHA256 with salt)
and JWT generation/verification using PyJWT.
Also supports backward-compatible verification of SHA-256 demo hashes.
"""

import hashlib
import hmac
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional
import jwt
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from backend.app.config import settings

bearer_scheme = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    """
    Hashes a password with PBKDF2-HMAC-SHA256 and a random 16-byte salt.
    Format: pbkdf2_sha256$<iterations>$<salt_hex>$<hash_hex>
    """
    salt = secrets.token_hex(16)
    iterations = 350000
    pwd_bytes = password.encode("utf-8")
    salt_bytes = salt.encode("utf-8")
    key = hashlib.pbkdf2_hmac("sha256", pwd_bytes, salt_bytes, iterations)
    return f"pbkdf2_sha256${iterations}${salt}${key.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies a plain password against the stored hash.
    Supports PBKDF2-SHA256 (primary) and raw SHA-256 hex (legacy, for hashes
    created by early frontend code). Plaintext comparisons are never performed.
    """
    if hashed_password.startswith("pbkdf2_sha256$"):
        parts = hashed_password.split("$")
        if len(parts) == 4:
            iterations = int(parts[1])
            salt = parts[2]
            stored_key = parts[3]
            test_key = hashlib.pbkdf2_hmac(
                "sha256",
                plain_password.encode("utf-8"),
                salt.encode("utf-8"),
                iterations
            ).hex()
            return hmac.compare_digest(stored_key, test_key)
        # Malformed PBKDF2 hash — reject
        return False

    # Legacy path: raw SHA-256 hex (64-char hex string).
    # Only accepted for backward compatibility with passwords hashed by early
    # frontend code. New passwords are always stored as PBKDF2.
    if len(hashed_password) == 64 and all(c in "0123456789abcdef" for c in hashed_password):
        raw_sha256 = hashlib.sha256(plain_password.encode("utf-8")).hexdigest()
        return hmac.compare_digest(raw_sha256, hashed_password)

    # Unknown format — reject without revealing details
    return False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Creates a signed JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """Decodes and validates a JWT token."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None


def get_current_user_id(credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme)) -> Optional[str]:
    """Extracts user_id from Bearer token if present."""
    if not credentials:
        return None
    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing user identity",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user_id
