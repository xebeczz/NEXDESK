"""User model — employees and administrators."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, gen_uuid, utcnow
from app.models.enums import UserRole


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    username: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        String(20), default=UserRole.USER, nullable=False
    )
    department: Mapped[str | None] = mapped_column(String(120), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Settings
    theme_preference: Mapped[str] = mapped_column(String(20), default="system", nullable=False)
    notification_preferences: Mapped[str | None] = mapped_column(Text, nullable=True)
    two_factor_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    two_factor_secret: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_password_change: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Password reset
    password_reset_token: Mapped[str | None] = mapped_column(String(255), nullable=True)
    password_reset_expires: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Last successful login (audit friendly)
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships (strings to avoid circular imports)
    created_tickets = relationship("Ticket", foreign_keys="Ticket.created_by_id", back_populates="created_by")
    assigned_tickets = relationship("Ticket", foreign_keys="Ticket.assigned_to_id", back_populates="assigned_to")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    chat_sessions = relationship("ChatSession", back_populates="user", cascade="all, delete-orphan")

    def touch_login(self) -> None:
        self.last_login_at = utcnow()

    def get_notification_preferences(self) -> dict:
        import json
        if self.notification_preferences:
            try:
                return json.loads(self.notification_preferences)
            except Exception:
                pass
        return {
            "email_notifications": True,
            "push_notifications": True,
            "ticket_updates": True,
            "ticket_assignments": True,
            "mentions": True,
            "comments": True,
            "weekly_digest": False,
        }

    def set_notification_preferences(self, prefs: dict) -> None:
        import json
        self.notification_preferences = json.dumps(prefs)
