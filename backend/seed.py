"""Database seed script.

Creates the two role users (admin / user) from env vars.
Optional: `python seed.py --with-sample-tickets` adds a small realistic set of
tickets per department/priority so the dashboard demos with real (inserted)
data. Default run only creates users — the application itself is data-driven.

Usage:
    uv run python seed.py            # users only
    uv run python seed.py --with-sample-tickets
"""
from __future__ import annotations

import argparse
import random
from datetime import timedelta

from app.core.config import settings
from app.core.security import hash_password
from app.db.base import utcnow
from app.db.session import SessionLocal
from app.models.enums import TicketPriority, UserRole
from app.models.ticket import (
    Ticket,
    TicketActivity,
    compute_sla_status,
    sla_deadline_for,
)
from app.models.user import User

SAMPLE_DATA = [
    ("Cannot access corporate VPN", "vpn", "VPN fails to connect from home office for the past hour.", UserRole.ADMIN, "Network & VPN", TicketPriority.HIGH, "open"),
    ("Email not syncing on mobile", "email", "Outlook mobile client stops syncing after the weekend.", UserRole.USER, "IT Support", TicketPriority.MEDIUM, "open"),
    ("Printer offline at floor 3", "printer", "Network printer shows offline; jobs stuck in queue.", UserRole.ADMIN, "IT Support", TicketPriority.MEDIUM, "in_progress"),
    ("Database replication lag spans 40 minutes", "database", "Production replica lag suggests a possible outage, several teams affected.", UserRole.ADMIN, "IT Operations", TicketPriority.CRITICAL, "open"),
    ("Laptop won't boot, hardware failure suspected", "hardware", "Employee laptop fails to POST; disks click.", UserRole.USER, "Hardware", TicketPriority.HIGH, "pending"),
    ("Slack login 2FA not working", "authentication", "2FA push not received after enabling device auth.", UserRole.USER, "Identity", TicketPriority.LOW, "open"),
    ("Install data analysis Toolkit on workstation", "software", "Need Python/coding analysis software installed and licensed.", UserRole.USER, "Software", TicketPriority.LOW, "resolved"),
]


def _next_ticket_no(db, day_label: str) -> str:
    from sqlalchemy import func
    from app.models.ticket import Ticket as T
    count = db.query(func.count(T.id)).filter(T.ticket_no.like(f"TCK-{day_label}-%")).scalar() or 0
    return f"TCK-{day_label}-{count + 1:04d}"


def seed_users(db) -> dict[str, User]:
    now = utcnow()
    specs = [
        (settings.SEED_ADMIN_EMAIL, "admin", "System Administrator", settings.SEED_ADMIN_PASSWORD, UserRole.ADMIN, "IT Operations"),
        (settings.SEED_USER_EMAIL, "user", "Demo Employee", settings.SEED_USER_PASSWORD, UserRole.USER, "HR"),
    ]
    created: dict[str, User] = {}
    for email, username, name, pwd, role, dept in specs:
        existing = db.query(User).filter(User.email == email).one_or_none()
        if existing is not None:
            created[role.value] = existing
            continue
        user = User(
            email=email,
            username=username,
            full_name=name,
            hashed_password=hash_password(pwd),
            role=role,
            department=dept,
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        db.add(user)
        created[role.value] = user
    db.commit()
    return created


def seed_sample_tickets(db, users: dict[str, User], count: int = 10) -> list[Ticket]:
    day_label = utcnow().strftime("%Y%m%d")
    admin = users["admin"]
    employee = users["user"]
    created = []
    now = utcnow()

    # Build a deterministic-ish timeline over the past ~30 days for chart demo.
    t = now
    for i in range(count):
        entry = SAMPLE_DATA[i % len(SAMPLE_DATA)]
        title, category, desc, requester_role, department, priority, status = entry
        requester = {"admin": admin, "user": employee}.get(
            requester_role.value, employee
        )
        created_at = t - timedelta(days=random.randint(1, 8), hours=i)
        deadline = sla_deadline_for(priority, created_at)
        resolved_at = created_at + timedelta(hours=6) if status in ("resolved", "closed") else None
        ticket = Ticket(
            ticket_no=_next_ticket_no(db, created_at.strftime("%Y%m%d")),
            title=title,
            description=desc,
            category=category,
            priority=priority,
            status=status,
            department=department,
            created_by_id=requester.id,
            assigned_to_id=admin.id if status != "open" else None,
            resolution_notes="Ticket processed by IT Support." if status in ("resolved", "closed") else None,
            sla_status=compute_sla_status(created_at, deadline, now),
            sla_deadline=deadline,
            created_at=created_at,
            updated_at=now,
            resolved_at=resolved_at,
            closed_at=resolved_at,
        )
        db.add(ticket)
        db.flush()
        db.add(
            TicketActivity(
                ticket_id=ticket.id,
                user_id=admin.id if status != "open" else requester.id,
                action="created" if i % 3 == 0 else "status_changed",
                field="status" if i % 3 == 0 else None,
                new_value=status,
                created_at=created_at + timedelta(minutes=5),
            )
        )
        created.append(ticket)
    db.commit()
    return created


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed ITDesk database")
    parser.add_argument("--with-sample-tickets", action="store_true")
    args = parser.parse_args()
    db = SessionLocal()
    try:
        users = seed_users(db)
        print(f"Seeded users: {', '.join(sorted(users))}")
        if args.with_sample_tickets:
            created = seed_sample_tickets(db, users)
            print(f"Seeded {len(created)} sample tickets.")
    finally:
        db.close()


if __name__ == "__main__":
    main()