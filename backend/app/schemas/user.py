"""User schemas."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.enums import UserRole


class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=100)
    full_name: str = Field(min_length=1, max_length=255)
    department: str | None = Field(default=None, max_length=120)


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)
    role: UserRole = Field(default=UserRole.USER)
    admin_registration_code: str | None = Field(default=None, max_length=64)


class UserRead(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    role: UserRole
    is_active: bool
    last_login_at: datetime | None = None
    created_at: datetime


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, max_length=255)
    department: str | None = Field(default=None, max_length=120)
    is_active: bool | None = None
    role: UserRole | None = None


class UserPasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=128)