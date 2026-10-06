"""Authentication schemas."""
from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field

from app.models.enums import UserRole
from app.schemas.user import UserRead


class LoginRequest(BaseModel):
    identifier: str = Field(min_length=3, max_length=255)  # email or username
    password: str = Field(min_length=1, max_length=128)
    role: UserRole | None = Field(default=None, description="Optional role to login as")


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)