"""Ticket, comment, activity, and attachment models."""
from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, gen_uuid, utcnow
from app.models.enums import SlaStatus, TicketPriority

# Deadline hours granted per priority (SLA clock).
PRIORITY_SLA_HOURS: dict[TicketPriority, int] = {
    TicketPriority.CRITICAL: 4,
    TicketPriority.HIGH: 8,
    TicketPriority.MEDIUM: 24,
    TicketPriority.LOW: 72,
}

# Threshold fraction of the SLA window after which status becomes "warning".
_WARNING_FRACTION = 0.75


def compute_sla_status(created_at: datetime, deadline: datetime, now: datetime | None = None) -> SlaStatus:
    now = now or utcnow()
    total = (deadline - created_at).total_seconds()
    if total <= 0:
        return SlaStatus.BREACHED
    remaining = (deadline - now).total_seconds()
    if remaining <= 0:
        return SlaStatus.BREACHED
    if remaining <= total * (1 - _WARNING_FRACTION):
        return SlaStatus.WARNING
    return SlaStatus.WITHIN_SLA


def sla_deadline_for(priority: TicketPriority, created_at: datetime) -> datetime:
    hours = PRIORITY_SLA_HOURS.get(priority, PRIORITY_SLA_HOURS[TicketPriority.MEDIUM])
    return created_at + timedelta(hours=hours)


class Ticket(Base, TimestampMixin):
    __tablename__ = "tickets"
    __table_args__ = (
        Index("ix_tickets_status_priority", "status", "priority"),
        Index("ix_tickets_department_created", "department", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    ticket_no: Mapped[str] = mapped_column(String(40), unique=True, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(80), nullable=False, default="General")
    priority: Mapped[TicketPriority] = mapped_column(
        String(20), default=TicketPriority.MEDIUM, nullable=False
    )
    status: Mapped[str] = mapped_column(String(20), default="open", nullable=False)
    department: Mapped[str | None] = mapped_column(String(120), nullable=True)
    resolution_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    similar_ticket_ids: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # SLA
    sla_status: Mapped[SlaStatus] = mapped_column(
        String(20), default=SlaStatus.WITHIN_SLA, nullable=False
    )
    sla_deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_by_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), index=True, nullable=False
    )
    assigned_to_id: Mapped[str | None] = mapped_column(
        "assigned_engineer_id", String(36), ForeignKey("users.id"), index=True, nullable=True
    )

    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_by = relationship("User", foreign_keys=[created_by_id], back_populates="created_tickets")
    assigned_to = relationship("User", foreign_keys=[assigned_to_id], back_populates="assigned_tickets")
    comments = relationship(
        "TicketComment", back_populates="ticket", cascade="all, delete-orphan", order_by="TicketComment.created_at"
    )
    activities = relationship(
        "TicketActivity", back_populates="ticket", cascade="all, delete-orphan", order_by="TicketActivity.created_at"
    )
    attachments = relationship(
        "TicketAttachment", back_populates="ticket", cascade="all, delete-orphan", order_by="TicketAttachment.uploaded_at"
    )

    @property
    def sla_hours(self) -> int:
        return PRIORITY_SLA_HOURS.get(self.priority, 24)


class TicketComment(Base, TimestampMixin):
    __tablename__ = "ticket_comments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ticket_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("tickets.id", ondelete="CASCADE"), index=True, nullable=False
    )
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    ticket = relationship("Ticket", back_populates="comments")
    user = relationship("User")


class TicketActivity(Base):
    __tablename__ = "ticket_activities"
    __table_args__ = (Index("ix_activity_ticket", "ticket_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ticket_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(40), nullable=False)  # e.g. "created", "status_changed"
    field: Mapped[str | None] = mapped_column(String(40), nullable=True)
    old_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    new_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )

    ticket = relationship("Ticket", back_populates="activities")
    user = relationship("User")


class TicketAttachment(Base):
    __tablename__ = "ticket_attachments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    ticket_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("tickets.id", ondelete="CASCADE"), index=True, nullable=False
    )
    uploader_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    size: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    content_type: Mapped[str] = mapped_column(String(120), nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )

    ticket = relationship("Ticket", back_populates="attachments")
    uploader = relationship("User")