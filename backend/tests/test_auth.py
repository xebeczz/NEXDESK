"""Authentication + authorization tests."""
from __future__ import annotations

from app.core.config import settings
from app.models.enums import UserRole

from tests.conftest import make_user


def test_register_and_login(client, db):
    res = client.post(
        "/api/v1/auth/register",
        json={
            "email": "new@test.io",
            "username": "newuser",
            "full_name": "New User",
            "password": "Secret@123",
            "department": "IT Support",
        },
    )
    assert res.status_code == 201, res.text
    data = res.json()
    assert data["access_token"]
    assert data["user"]["email"] == "new@test.io"
    # Registration defaults to USER role.
    assert data["user"]["role"] == UserRole.USER.value


def test_login_with_email(client, db):
    user = make_user(db, role=UserRole.USER.value)
    res = client.post(
        "/api/v1/auth/login",
        json={"identifier": user.email, "password": "Password@123", "role": "user"},
    )
    assert res.status_code == 200, res.text
    assert res.json()["access_token"]
    assert res.json()["user"]["role"] == UserRole.USER.value


def test_login_with_username(client, db):
    user = make_user(db)
    res = client.post(
        "/api/v1/auth/login",
        json={"identifier": user.username, "password": "Password@123", "role": "user"},
    )
    assert res.status_code == 200, res.text
    assert res.json()["user"]["username"] == user.username


def test_login_wrong_password(client, db):
    user = make_user(db)
    res = client.post(
        "/api/v1/auth/login",
        json={"identifier": user.email, "password": "Wrong@123", "role": "user"},
    )
    assert res.status_code == 401


def test_login_wrong_role(client, db):
    user = make_user(db, role=UserRole.USER.value)
    res = client.post(
        "/api/v1/auth/login",
        json={"identifier": user.email, "password": "Password@123", "role": "admin"},
    )
    assert res.status_code == 403


def test_admin_login_with_correct_role(client, db):
    admin = make_user(db, role=UserRole.ADMIN.value)
    res = client.post(
        "/api/v1/auth/login",
        json={"identifier": admin.email, "password": "Password@123", "role": "admin"},
    )
    assert res.status_code == 200, res.text
    assert res.json()["user"]["role"] == UserRole.ADMIN.value


def test_me_requires_token(client, db):
    res = client.get("/api/v1/auth/me")
    assert res.status_code == 401


def test_me_returns_user(client, db, auth_headers):
    user = make_user(db)
    headers = auth_headers(user)
    res = client.get("/api/v1/auth/me", headers=headers)
    assert res.status_code == 200
    assert res.json()["email"] == user.email


def test_register_admin_with_valid_code(client, db):
    res = client.post(
        "/api/v1/auth/register",
        json={
            "email": "admin@test.io",
            "username": "adminuser",
            "full_name": "Admin User",
            "password": "AdminPass@123",
            "role": "admin",
            "admin_registration_code": settings.ADMIN_REGISTRATION_CODE,
        },
    )
    assert res.status_code == 201, res.text
    data = res.json()
    assert data["user"]["role"] == UserRole.ADMIN.value


def test_register_admin_without_code_fails(client, db):
    res = client.post(
        "/api/v1/auth/register",
        json={
            "email": "admin2@test.io",
            "username": "adminuser2",
            "full_name": "Admin User 2",
            "password": "AdminPass@123",
            "role": "admin",
        },
    )
    assert res.status_code == 400
    assert "Admin registration code is required" in res.json()["detail"]


def test_register_admin_with_invalid_code_fails(client, db):
    res = client.post(
        "/api/v1/auth/register",
        json={
            "email": "admin3@test.io",
            "username": "adminuser3",
            "full_name": "Admin User 3",
            "password": "AdminPass@123",
            "role": "admin",
            "admin_registration_code": "INVALID-CODE",
        },
    )
    assert res.status_code == 400
    assert "Invalid admin registration code" in res.json()["detail"]


def test_admin_guard(client, db, auth_headers):
    admin = make_user(db, role=UserRole.ADMIN.value)
    employee = make_user(db, role=UserRole.USER.value)

    admin_ok = client.get("/api/v1/admin/users", headers=auth_headers(admin))
    assert admin_ok.status_code == 200

    employee_forbidden = client.get("/api/v1/admin/users", headers=auth_headers(employee))
    assert employee_forbidden.status_code == 403


def test_admin_report_allowed(client, db, auth_headers):
    admin = make_user(db, role=UserRole.ADMIN.value)
    res = client.get("/api/v1/reports/summary", headers=auth_headers(admin))
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/pdf"


def test_employee_report_forbidden(client, db, auth_headers):
    employee = make_user(db, role=UserRole.USER.value)
    res = client.get("/api/v1/reports/summary", headers=auth_headers(employee))
    assert res.status_code == 403


def test_forgot_and_reset_password(client, db):
    user = make_user(db)
    res = client.post("/api/v1/auth/forgot-password", json={"email": user.email})
    assert res.status_code in (200, 202)

    # Read the reset token the backend stored on the user record.
    db.refresh(user)
    token = user.password_reset_token
    assert token

    res = client.post(
        "/api/v1/auth/reset-password",
        json={"token": token, "new_password": "NewPass@456"},
    )
    assert res.status_code == 200, res.text

    # Old password no longer works; new one does.
    res = client.post(
        "/api/v1/auth/login",
        json={"identifier": user.email, "password": "Password@123"},
    )
    assert res.status_code == 401
    res = client.post(
        "/api/v1/auth/login",
        json={"identifier": user.email, "password": "NewPass@456"},
    )
    assert res.status_code == 200