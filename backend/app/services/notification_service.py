"""Notification persistence + real-time fan-out via the event hub."""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.notification import Notification
from app.services.event_hub import event_hub


def create_notification(
    db: Session,
    user_id: str,
    notification_type: str,
    title: str,
    message: str,
    ticket_id: str | None = None,
    *,
    commit: bool = True,
) -> Notification:
    notification = Notification(
        user_id=user_id,
        type=notification_type,
        title=title,
        message=message,
        ticket_id=ticket_id,
    )
    db.add(notification)
    db.flush()
    # Real-time fan-out to live SSE subscribers for this user.
    event_hub.publish(
        user_id,
        {
            "type": "notification",
            "notification": {
                "id": notification.id,
                "type": notification.type,
                "title": notification.title,
                "message": notification.message,
                "ticket_id": notification.ticket_id,
                "is_read": notification.is_read,
                "created_at": notification.created_at.isoformat() if notification.created_at else None,
            },
        },
    )
    if commit:
        db.commit()
    return notification