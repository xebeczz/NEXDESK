"""Dashboard + analytics role-scoping tests."""
from __future__ import annotations

from tests.conftest import make_user


def test_dashboard_stats_real_counts(client, db, auth_headers):
    admin = make_user(db, role="admin")
    headers = auth_headers(admin)
    for i in range(3):
        client.post(
            "/api/v1/tickets",
            json={"title": f"Ticket {i}", "description": "desc", "category": "General", "priority": "medium"},
            headers=headers,
        )
    res = client.get("/api/v1/dashboard/stats", headers=headers)
    assert res.status_code == 200
    stats = res.json()
    assert stats["total"] == 3
    assert stats["open"] == 3
    assert stats["priority_counts"]["medium"] == 3


def test_analytics_distributions_shape(client, db, auth_headers):
    admin = make_user(db, role="admin")
    headers = auth_headers(admin)
    client.post(
        "/api/v1/tickets",
        json={"title": "Mail down", "description": "Email not sending", "category": "Email", "priority": "high"},
        headers=headers,
    )
    priority = client.get("/api/v1/analytics/priority-distribution", headers=headers).json()
    assert any(p["priority"] == "high" and p["count"] == 1 for p in priority["items"])

    trend = client.get("/api/v1/analytics/tickets-over-time", params={"days": 7}, headers=headers).json()
    assert len(trend["items"]) == 7


def test_analytics_role_scoped(client, db, auth_headers):
    alice = make_user(db, role="user", department="HR")
    carol = make_user(db, role="user", department="HR")
    client.post(
        "/api/v1/tickets",
        json={"title": "Alice ticket", "description": "desc", "category": "General", "priority": "low"},
        headers=auth_headers(alice),
    )
    client.post(
        "/api/v1/tickets",
        json={"title": "Bob ticket", "description": "desc", "category": "General", "priority": "low"},
        headers=auth_headers(carol),
    )
    stats = client.get("/api/v1/dashboard/stats", headers=auth_headers(alice)).json()
    # Employee Alice only sees her own single ticket, not Bob's.
    assert stats["total"] == 1