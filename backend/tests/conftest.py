"""Shared pytest fixtures: isolated in-memory DB + FastAPI test client."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import hash_password
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.enums import UserRole
from app.models.user import User

# StaticPool keeps a single shared connection so every thread (including the
# TestClient's worker pool) sees the same in-memory database.
_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    future=True,
)
_TestSession = sessionmaker(bind=_engine, autocommit=False, autoflush=False, future=True)


@pytest.fixture()
def db():
    Base.metadata.create_all(_engine)
    session = _TestSession()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(_engine)


@pytest.fixture()
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def make_user(
    db,
    role: str = UserRole.USER.value,
    email: str | None = None,
    username: str | None = None,
    password: str = "Password@123",
    department: str | None = "IT Support",
) -> User:
    import uuid

    idx = uuid.uuid4().hex[:8]
    user = User(
        email=email or f"{idx}@test.io",
        username=username or f"user_{idx}",
        full_name=f"Tester {idx}",
        role=role,
        department=department,
        hashed_password=hash_password(password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture()
def auth_headers(client, db):
    """Return a callable that logs a user in and yields bearer headers."""

    def _login(user):
        res = client.post(
            "/api/v1/auth/login",
            json={"identifier": user.email, "password": "Password@123"},
        )
        assert res.status_code == 200, res.text
        token = res.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    return _login