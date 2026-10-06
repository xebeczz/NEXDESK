"""Shared response schemas."""
from __future__ import annotations

from pydantic import BaseModel


class MessageResponse(BaseModel):
    message: str


class Paginated(BaseModel):
    total: int
    page: int
    page_size: int
    pages: int


class ListResponse(BaseModel):
    items: list
    total: int
    page: int
    page_size: int
    pages: int
