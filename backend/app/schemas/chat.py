"""AI chat and ticket-draft schemas."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ChatMessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: str
    role: str
    content: str
    intent: str | None = None
    created_at: datetime


class ChatSessionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    message_count: int = 0


class ChatSessionCreate(BaseModel):
    title: str | None = Field(default=None, max_length=255)


class ChatSendRequest(BaseModel):
    message: str = Field(min_length=1, max_length=8000)


class AiAnalysis(BaseModel):
    """Validated structured response produced by the AI and checked by the backend."""
    intent: str
    confidence: float = Field(ge=0.0, le=1.0)
    priority: str = Field(default="medium")
    category: str = Field(default="General")
    department: str | None = None
    summary: str
    should_create_ticket: bool


class AiTicketDraftRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    description: str
    category: str
    priority: str
    department: str | None = None
    confidence: float
    intent: str | None = None
    status: str
    created_at: datetime