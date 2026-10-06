"""Application configuration loaded from environment variables / .env file."""
from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # App
    APP_NAME: str = "ITDesk — AI Ticket Management System"
    APP_ENV: str = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    # Security
    SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Frontend
    FRONTEND_ORIGIN: str = "http://localhost:5173"

    # Database
    DATABASE_URL: str = "sqlite:///./data/itdesk.db"

    # AI / NVIDIA (backend-only secret)
    NVIDIA_API_KEY: str = ""
    NVIDIA_MODEL: str = "nvidia/nemotron-3-ultra-550b-a55b"
    NVIDIA_BASE_URL: str = "https://integrate.api.nvidia.com/v1"

    # SMTP (optional)
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "no-reply@itdesk.io"

    # Uploads
    UPLOAD_DIR: str = "./uploads"

    # Seed credentials (dev only — read from .env by seed.py)
    SEED_ADMIN_EMAIL: str = "admin@itdesk.io"
    SEED_ADMIN_PASSWORD: str = "Admin@12345"
    SEED_USER_EMAIL: str = "user@itdesk.io"
    SEED_USER_PASSWORD: str = "User@12345"

    # Admin registration (required when registering with role=admin)
    ADMIN_REGISTRATION_CODE: str = "ITDESK-ADMIN-2024"

    @property
    def cors_origins(self) -> List[str]:
        return [o.strip() for o in self.FRONTEND_ORIGIN.split(",") if o.strip()]

    @field_validator("NVIDIA_MODEL")
    @classmethod
    def _strip_model(cls, v: str) -> str:
        return v.strip()

    @property
    def is_ai_enabled(self) -> bool:
        return bool(self.NVIDIA_API_KEY)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()