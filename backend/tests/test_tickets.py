"""Ticket management workflow + role-scoping tests."""
from __future__ import annotations

from app.models.enums import TicketStatus, UserRole

from tests.conftest import make_user


def _create(client, headers, **overrides):
    payload = {
        "title": "Laptop won't boot",
        "description": "Blue screen on startup",
        "category": "Hardware",
        "priority": "high",
    }
    payload.update(overrides)
    return client.post("/api/v1/tickets", json=payload, headers=headers)


def test_employee_creates_ticket(client, db, auth_headers):
    employee = make_user(db, department="Finance")
    headers = auth_headers(employee)
    res = _create(client, headers)
    assert res.status_code == 201, res.text
    body = res.json()
    assert body["status"] == TicketStatus.OPEN.value
    assert body["created_by"]["id"] == employee.id
    # Department defaults to the user's department.
    assert body["department"] == "Finance"
    assert body["ticket_no"].startswith("TCK-")


def test_employee_cannot_assign_at_creation(client, db, auth_headers):
    employee = make_user(db)
    admin = make_user(db, role=UserRole.ADMIN.value)
    headers = auth_headers(employee)
    res = _create(client, headers, assigned_to_id=admin.id)
    assert res.status_code == 403


def test_admin_can_assign_at_creation(client, db, auth_headers):
    admin = make_user(db, role=UserRole.ADMIN.value)
    employee = make_user(db)
    headers = auth_headers(admin)
    res = _create(client, headers, assigned_to_id=employee.id)
    assert res.status_code == 201, res.text
    assert res.json()["assigned_to"]["id"] == employee.id


def test_employee_sees_only_own_tickets(client, db, auth_headers):
    alice = make_user(db, department="HR")
    bob = make_user(db, department="HR")
    _create(client, auth_headers(alice))
    _create(client, auth_headers(bob))

    res = client.get("/api/v1/tickets", headers=auth_headers(alice))
    items = res.json()["items"]
    assert all(t["created_by"]["id"] == alice.id for t in items)


def test_assign_and_close_reopen(client, db, auth_headers):
    admin = make_user(db, role=UserRole.ADMIN.value)
    admin2 = make_user(db, role=UserRole.ADMIN.value)
    employee = make_user(db)
    headers = auth_headers(admin)

    ticket = _create(client, headers).json()

    assigned = client.post(f"/api/v1/tickets/{ticket['id']}/assign", json={"assigned_to_id": admin2.id}, headers=headers)
    assert assigned.status_code == 200
    assert assigned.json()["assigned_to"]["id"] == admin2.id

    closed = client.post(f"/api/v1/tickets/{ticket['id']}/close", json={"resolution_notes": "Rebooted successfully"}, headers=headers)
    assert closed.status_code == 200
    assert closed.json()["status"] == TicketStatus.CLOSED.value
    assert closed.json()["resolution_notes"] == "Rebooted successfully"

    reopened = client.post(f"/api/v1/tickets/{ticket['id']}/reopen", headers=headers)
    assert reopened.status_code == 200
    assert reopened.json()["status"] == TicketStatus.OPEN.value


def test_add_comment_and_activity(client, db, auth_headers):
    admin = make_user(db, role=UserRole.ADMIN.value)
    headers = auth_headers(admin)
    ticket = _create(client, headers).json()

    res = client.post(f"/api/v1/tickets/{ticket['id']}/comments", json={"content": "Investigating"}, headers=headers)
    assert res.status_code == 201

    comments = client.get(f"/api/v1/tickets/{ticket['id']}/comments", headers=headers)
    assert len(comments.json()) == 1
    assert comments.json()[0]["content"] == "Investigating"

    activities = client.get(f"/api/v1/tickets/{ticket['id']}/activities", headers=headers)
    assert activities.status_code == 200
    assert any(a["action"] == "created" for a in activities.json())


def test_employee_cannot_delete(client, db, auth_headers):
    admin = make_user(db, role=UserRole.ADMIN.value)
    employee = make_user(db)
    ticket = _create(client, auth_headers(admin)).json()

    res = client.delete(f"/api/v1/tickets/{ticket['id']}", headers=auth_headers(employee))
    assert res.status_code == 403


def test_admin_can_delete(client, db, auth_headers):
    admin = make_user(db, role=UserRole.ADMIN.value)
    ticket = _create(client, auth_headers(admin)).json()
    res = client.delete(f"/api/v1/tickets/{ticket['id']}", headers=auth_headers(admin))
    assert res.status_code == 200