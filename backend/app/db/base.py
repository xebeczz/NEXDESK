"""Declarative base and shared mixins for all ORM models."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, MetaData
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# Use explicit naming conventions so Alembic can generate clean migrations.
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

metadata = MetaData(naming_convention=NAMING_CONVENTION)


def utcnow() -> datetime:
    """Timezone-aware UTC now. Naive datetimes from SQLite are normalized on read."""
    return datetime.now(timezone.utc)


def ensure_aware(value: datetime | None) -> datetime | None:
    """Return a timezone-aware UTC datetime.

    SQLite stores ``DateTime(timezone=True)`` columns as naive UTC; PostgreSQL
    stores them aware. Normalizing on read keeps comparisons correct on both.
    """
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


class Base(DeclarativeBase):
    metadata = metadata


def gen_uuid() -> str:
    return str(uuid.uuid4())


class TimestampMixin:
    """Adds created_at / updated_at columns that the app maintains."""
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )