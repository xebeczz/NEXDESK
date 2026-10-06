"""Import all models so Alembic autogenerate and app startup see every table."""
from app.models.audit_log import AuditLog
from app.models.chat import ChatMessage, ChatSession
from app.models.enums import (
    ChatRole,
    DraftStatus,
    NotificationType,
    SlaStatus,
    TicketPriority,
    TicketStatus,
    UserRole,
)
from app.models.notification import AiTicketDraft, Notification
from app.models.ticket import (
    PRIORITY_SLA_HOURS,
    Ticket,
    TicketActivity,
    TicketAttachment,
    TicketComment,
    compute_sla_status,
    sla_deadline_for,
)
from app.models.user import User

__all__ = [
    "User",
    "Ticket",
    "TicketComment",
    "TicketActivity",
    "TicketAttachment",
    "ChatSession",
    "ChatMessage",
    "Notification",
    "AiTicketDraft",
    "AuditLog",
    "UserRole",
    "TicketStatus",
    "TicketPriority",
    "SlaStatus",
    "ChatRole",
    "NotificationType",
    "DraftStatus",
    "PRIORITY_SLA_HOURS",
    "compute_sla_status",
    "sla_deadline_for",
]