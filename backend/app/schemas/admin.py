"""Response schemas for admin endpoints."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class SystemHealth(BaseModel):
    status: str
    uptime_seconds: float | None = None
    environment: str
    db_status: str
    db_query_ms: float | None = None
    total_users: int = 0
    total_tickets: int = 0
    active_tickets: int = 0
    pending_drafts: int = 0


class AuditEntry(BaseModel):
    id: int
    actor: str | None = None
    action: str
    entity_type: str | None = None
    entity_id: str | None = None
    details: dict | None = None
    created_at: datetime


class AuditListResponse(BaseModel):
    items: list[AuditEntry]
    total: int
    page: int
    page_size: int
    pages: int