"""Ticket persistence, numbering, SLA, permissions, and activity helpers."""
from __future__ import annotations

from datetime import timedelta

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.db.base import ensure_aware, utcnow
from app.models.enums import UserRole
from app.models.ticket import (
    Ticket,
    TicketActivity,
    compute_sla_status,
    sla_deadline_for,
)
from app.models.user import User


def next_ticket_no(db: Session, now=None) -> str:
    now = now or utcnow()
    day_label = now.strftime("%Y%m%d")
    prefix = f"TCK-{day_label}-"
    count = db.query(func.count(Ticket.id)).filter(Ticket.ticket_no.like(prefix + "%")).scalar() or 0
    return f"{prefix}{count + 1:04d}"


def apply_sla(ticket: Ticket, now=None) -> None:
    # The SLA clock starts at creation; priorities keep a stable deadline.
    start = ensure_aware(ticket.created_at) or now or utcnow()
    if ticket.sla_deadline is None:
        ticket.sla_deadline = sla_deadline_for(ticket.priority, start)
    ticket.sla_status = compute_sla_status(start, ensure_aware(ticket.sla_deadline), now)


def log_activity(
    db,
    ticket: Ticket,
    actor: User | None,
    action: str,
    *,
    field: str | None = None,
    old_value: str | None = None,
    new_value: str | None = None,
) -> None:
    from app.models.ticket import TicketActivity

    db.add(
        TicketActivity(
            ticket_id=ticket.id,
            user_id=actor.id if actor else None,
            action=action,
            field=field,
            old_value=old_value,
            new_value=new_value,
            created_at=utcnow(),
        )
    )


# --- Permissions ---
def user_visible_query(db: Session, user: User):
    """Base query restricted to what the user is allowed to see."""
    q = db.query(Ticket)
    if user.role == UserRole.ADMIN:
        return q
    return q.filter(Ticket.created_by_id == user.id)


def can_view(user: User, ticket: Ticket) -> bool:
    if user.role == UserRole.ADMIN:
        return True
    return ticket.created_by_id == user.id


def can_manage(user: User, ticket: Ticket) -> bool:
    if user.role == UserRole.ADMIN:
        return True
    return ticket.created_by_id == user.id


# --- Builders ---
def build_detail(ticket: Ticket) -> dict:
    """Assemble a TicketDetail dict (comments + activities + attachments)."""
    from app.schemas.ticket import (
        TicketActivityRead,
        TicketAttachmentRead,
        TicketCommentRead,
        TicketRead,
    )

    detail = TicketRead.model_validate(ticket)
    return {
        **detail.model_dump(),
        "comments": [
            {**TicketCommentRead.model_validate(c).model_dump(), "user": c.user and {
                "id": c.user.id, "username": c.user.username, "full_name": c.user.full_name,
                "email": c.user.email, "role": c.user.role, "department": c.user.department}}
            for c in ticket.comments
        ],
        "activities": [
            {**TicketActivityRead.model_validate(a).model_dump(), "user": None if not a.user else {
                "id": a.user.id, "username": a.user.username, "full_name": a.user.full_name,
                "email": a.user.email, "role": a.user.role, "department": a.user.department}}
            for a in ticket.activities
        ],
        "attachments": [
            {**TicketAttachmentRead.model_validate(at).model_dump(), "uploaded_by": None if not at.uploader else {
                "id": at.uploader.id, "username": at.uploader.username, "full_name": at.uploader.full_name,
                "email": at.uploader.email, "role": at.uploader.role, "department": at.uploader.department}}
            for at in ticket.attachments
        ],
    }