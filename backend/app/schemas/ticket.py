"""Ticket-related schemas."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import TicketPriority, TicketStatus
from app.schemas.common import ListResponse


class UserRef(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    username: str
    full_name: str
    email: str
    role: str
    department: str | None = None


class TicketBase(BaseModel):
    title: str = Field(min_length=3, max_length=255)
    description: str = Field(min_length=3)
    category: str = Field(default="General", min_length=1, max_length=80)
    priority: TicketPriority = TicketPriority.MEDIUM


class TicketCreate(TicketBase):
    department: str | None = Field(default=None, max_length=120)
    assigned_to_id: str | None = None
    similar_ticket_ids: list[str] | None = Field(default=None, max_length=100)


class TicketUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=255)
    description: str | None = Field(default=None, min_length=3)
    category: str | None = Field(default=None, min_length=1, max_length=80)
    priority: TicketPriority | None = None
    department: str | None = Field(default=None, max_length=120)
    resolution_notes: str | None = Field(default=None, max_length=5000)
    status: TicketStatus | None = None


class TicketRead(TicketBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    ticket_no: str
    status: TicketStatus
    sla_status: str
    sla_deadline: datetime | None = None
    department: str | None = None
    resolution_notes: str | None = None
    ai_summary: str | None = None
    similar_ticket_ids: list[str] | None = None
    created_by: UserRef
    assigned_to: UserRef | None = None
    created_at: datetime
    updated_at: datetime
    resolved_at: datetime | None = None
    closed_at: datetime | None = None

    @field_validator("similar_ticket_ids", mode="before")
    @classmethod
    def parse_similar_ids(cls, value: Any) -> list[str] | None:
        if value is None:
            return None
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            value = value.strip()
            if not value:
                return None
            return [item.strip() for item in value.split(",") if item.strip()]
        return None


class SimilarTicket(BaseModel):
    ticket_id: str
    ticket_no: str
    title: str
    description: str
    category: str
    priority: str
    status: str
    department: str | None = None
    created_at: datetime | None = None
    resolved_at: datetime | None = None
    closed_at: datetime | None = None
    resolution_notes: str | None = None
    ai_summary: str | None = None
    similarity: float
    created_by: UserRef | None = None


class SimilarTicketsResponse(BaseModel):
    similar_tickets: list[SimilarTicket]


class TicketCommentCreate(BaseModel):
    content: str = Field(min_length=1)


class TicketCommentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    content: str
    user: UserRef
    created_at: datetime


class TicketActivityRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    action: str
    field: str | None = None
    old_value: str | None = None
    new_value: str | None = None
    user: UserRef | None = None
    created_at: datetime


class TicketAttachmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    ticket_id: str
    filename: str
    size: int
    content_type: str
    uploaded_by: UserRef | None = None
    uploaded_at: datetime


class TicketDetail(TicketRead):
    comments: list[TicketCommentRead] = []
    activities: list[TicketActivityRead] = []
    attachments: list[TicketAttachmentRead] = []


class TicketListResponse(ListResponse):
    items: list[TicketRead]


class AssignRequest(BaseModel):
    assigned_to_id: str


class CloseRequest(BaseModel):
    resolution_notes: str | None = Field(default=None, max_length=5000)


class StatusChangeRequest(BaseModel):
    status: TicketStatus
    resolution_notes: str | None = Field(default=None, max_length=5000)
