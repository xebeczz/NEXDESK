"""Settings schemas for user preferences."""
from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field
from typing import Literal, Optional

from app.models.enums import UserRole


class ThemePreference(BaseModel):
    theme: Literal["light", "dark", "system"]


class NotificationPreferences(BaseModel):
    email_notifications: bool = True
    push_notifications: bool = True
    ticket_updates: bool = True
    ticket_assignments: bool = True
    mentions: bool = True
    comments: bool = True
    weekly_digest: bool = False


class SecuritySettings(BaseModel):
    two_factor_enabled: bool = False
    last_password_change: Optional[str] = None


class ProfileUpdate(BaseModel):
    full_name: str = Field(min_length=1, max_length=255)
    department: Optional[str] = Field(default=None, max_length=120)
    username: str = Field(min_length=3, max_length=100)
    email: EmailStr


class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=128)


class SettingsResponse(BaseModel):
    user: "UserRead"
    theme_preference: ThemePreference
    notification_preferences: NotificationPreferences
    security_settings: SecuritySettings


# Import UserRead after definition to avoid circular import
from app.schemas.user import UserRead
SettingsResponse.model_rebuild()