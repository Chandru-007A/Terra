"""
Configuration settings for the TERRA Backend.
Uses Pydantic BaseSettings for robust environment variable management.

SECURITY NOTE: Always set JWT_SECRET via the environment (or .env file) in any
non-local deployment. The built-in default is intentionally insecure and is
provided only for local development convenience.
"""

import warnings
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

_INSECURE_DEFAULT_SECRET = "terra-super-secure-secret-key-change-in-production-2026"


class Settings(BaseSettings):
    APP_NAME: str = "TERRA Agricultural Optimization API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "sqlite:///./terra.db"

    # JWT & Authentication
    # IMPORTANT: Override JWT_SECRET with a strong random value in production.
    JWT_SECRET: str = _INSECURE_DEFAULT_SECRET
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000"
    ]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()

# Warn loudly if the insecure default JWT secret is still in use outside DEBUG mode
if not settings.DEBUG and settings.JWT_SECRET == _INSECURE_DEFAULT_SECRET:
    warnings.warn(
        "SECURITY WARNING: JWT_SECRET is set to the insecure default value. "
        "Set a strong random secret via the JWT_SECRET environment variable "
        "before deploying to production.",
        stacklevel=1,
    )

