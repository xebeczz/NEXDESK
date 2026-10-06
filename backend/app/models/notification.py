"""Notification and AI ticket draft models."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, gen_uuid, utcnow
from app.models.enums import DraftStatus


class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = (Index("ix_notif_user_read", "user_id", "is_read"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    type: Mapped[str] = mapped_column(String(40), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    ticket_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("tickets.id", ondelete="SET NULL"), nullable=True
    )
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )

    user = relationship("User", back_populates="notifications")
    ticket = relationship("Ticket")


class AiTicketDraft(Base, TimestampMixin):
    """A ticket the AI recommended — persisted before any ticket is created.
    The backend validates and, only after explicit user confirmation, promotes it."""

    __tablename__ = "ai_ticket_drafts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    chat_session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("chat_sessions.id", ondelete="CASCADE"), index=True, nullable=False
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(80), nullable=False)
    priority: Mapped[str] = mapped_column(String(20), nullable=False)
    department: Mapped[str | None] = mapped_column(String(120), nullable=True)
    confidence: Mapped[float] = mapped_column(default=0.0, nullable=False)
    intent: Mapped[str | None] = mapped_column(String(40), nullable=True)
    status: Mapped[DraftStatus] = mapped_column(
        String(20), default=DraftStatus.PENDING, nullable=False
    )
    created_ticket_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("tickets.id", ondelete="SET NULL"), nullable=True
    )

    chat_session = relationship("ChatSession")
    user = relationship("User")
    created_ticket = relationship("Ticket")