"""Domain enums shared across models and schemas."""
from __future__ import annotations

from enum import Enum


class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"


class TicketStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    PENDING = "pending"
    RESOLVED = "resolved"
    CLOSED = "closed"


class TicketPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SlaStatus(str, Enum):
    WITHIN_SLA = "within_sla"
    WARNING = "warning"
    BREACHED = "breached"


class ChatRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class NotificationType(str, Enum):
    TICKET_CREATED = "ticket_created"
    TICKET_ASSIGNED = "ticket_assigned"
    TICKET_UPDATED = "ticket_updated"
    TICKET_CLOSED = "ticket_closed"
    AI_RECOMMENDATION = "ai_recommendation"
    LOGIN_SUCCESS = "login_success"
    ERROR = "error"
    WARNING = "warning"
    TICKET_COMMENTED = "ticket_commented"


class DraftStatus(str, Enum):
    PENDING = "pending"
    CREATED = "created"
    DISMISSED = "dismissed"