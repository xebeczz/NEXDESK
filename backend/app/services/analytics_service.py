"""Dashboard + analytics aggregation.

Every figure here is computed from real data via SQL aggregates over the
Ticket table, always scoped by the requesting user's role (employees only see
their own tickets; admins see everything).
No values are hardcoded.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.enums import SlaStatus, TicketPriority, TicketStatus
from app.models.ticket import Ticket
from app.models.user import User
from app.services.ticket_service import user_visible_query


def _as_aware(dt):
    if dt is None:
        return datetime.now(timezone.utc)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _utc_iso(dt) -> str | None:
    if dt is None:
        return None
    return _as_aware(dt).astimezone(timezone.utc).isoformat()


def _visible_ids_select(db: Session, user: User):
    """Scalar subquery of visible ticket ids so aggregates stay role-scoped."""
    return user_visible_query(db, user).with_entities(Ticket.id).scalar_subquery()


def _keyed(db: Session, base, field):
    rows = db.query(field, func.count(Ticket.id))\
        .filter(Ticket.id.in_(base)).group_by(field).all()
    return {r[0]: int(r[1]) for r in rows}


# --- Dashboard KPI endpoint ---
def dashboard_stats(db: Session, user: User) -> dict:
    base = _visible_ids_select(db, user)

    status_map = _keyed(db, base, Ticket.status)
    priority_map = _keyed(db, base, Ticket.priority)
    sla_map = _keyed(db, base, Ticket.sla_status)

    total = sum(status_map.values())
    open_count = status_map.get(TicketStatus.OPEN.value, 0)
    in_progress = status_map.get(TicketStatus.IN_PROGRESS.value, 0)
    pending = status_map.get(TicketStatus.PENDING.value, 0)
    resolved = status_map.get(TicketStatus.RESOLVED.value, 0)
    closed = status_map.get(TicketStatus.CLOSED.value, 0)
    active = open_count + in_progress + pending

    high = priority_map.get(TicketPriority.HIGH.value, 0)
    critical = priority_map.get(TicketPriority.CRITICAL.value, 0)

    within = sla_map.get(SlaStatus.WITHIN_SLA.value, 0)
    warning = sla_map.get(SlaStatus.WARNING.value, 0)
    breached = sla_map.get(SlaStatus.BREACHED.value, 0)
    sla_measured = within + warning + breached
    sla_compliance = round((within / sla_measured) * 100, 1) if sla_measured else None

    now = _now()
    day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = day_start - timedelta(days=6)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    today_count = db.query(Ticket.id).filter(Ticket.id.in_(base), Ticket.created_at >= day_start).count()
    week_count = db.query(Ticket.id).filter(Ticket.id.in_(base), Ticket.created_at >= week_start).count()
    month_count = db.query(Ticket.id).filter(Ticket.id.in_(base), Ticket.created_at >= month_start).count()

    top_dept_row = db.query(Ticket.department, func.count(Ticket.id))\
        .filter(Ticket.id.in_(base), Ticket.department.isnot(None))\
        .group_by(Ticket.department).order_by(func.count(Ticket.id).desc()).first()
    top_department = top_dept_row[0] if top_dept_row else None

    resolved_rows = db.query(Ticket.created_at, Ticket.resolved_at)\
        .filter(Ticket.id.in_(base), Ticket.resolved_at.isnot(None)).all()
    hours = []
    for created, resolved_at in resolved_rows:
        c, r = _as_aware(created), _as_aware(resolved_at)
        if r > c:
            hours.append((r - c).total_seconds() / 3600.0)
    avg_res = round(sum(hours) / len(hours), 1) if hours else None

    return {
        "total": total,
        "open": open_count,
        "in_progress": in_progress,
        "pending": pending,
        "resolved": resolved,
        "closed": closed,
        "active": active,
        "unresolved": active,
        "high_priority": high,
        "critical": critical,
        "avg_resolution_hours": avg_res,
        "sla_compliance_percent": sla_compliance,
        "sla_breached": breached,
        "sla_warning": warning,
        "tickets_today": today_count,
        "tickets_this_week": week_count,
        "tickets_this_month": month_count,
        "top_department": top_department,
        "status_counts": {k.value: status_map.get(k.value, 0) for k in TicketStatus},
        "priority_counts": {k.value: priority_map.get(k.value, 0) for k in TicketPriority},
        "sla_counts": {k.value: sla_map.get(k.value, 0) for k in SlaStatus},
    }


# --- Trend / distribution endpoints ---
def tickets_over_time(db: Session, user: User, days: int = 30) -> list[dict]:
    base = _visible_ids_select(db, user)
    since = (_now() - timedelta(days=days - 1)).replace(hour=0, minute=0, second=0, microsecond=0)
    rows = db.query(func.date(Ticket.created_at).label("day"), func.count(Ticket.id))\
        .filter(Ticket.id.in_(base), Ticket.created_at >= since)\
        .group_by(func.date(Ticket.created_at)).all()
    by_day = {str(r[0]): int(r[1]) for r in rows}
    out = []
    for i in range(days):
        day = (since + timedelta(days=i)).date()
        out.append({"date": day.isoformat(), "count": by_day.get(day.isoformat(), 0)})
    return out


def priority_distribution(db: Session, user: User) -> list[dict]:
    base = _visible_ids_select(db, user)
    counts = _keyed(db, base, Ticket.priority)
    return [{"priority": p.value, "count": counts.get(p.value, 0)} for p in TicketPriority]


def status_distribution(db: Session, user: User) -> list[dict]:
    base = _visible_ids_select(db, user)
    counts = _keyed(db, base, Ticket.status)
    return [{"status": s.value, "count": counts.get(s.value, 0)} for s in TicketStatus]


def department_distribution(db: Session, user: User) -> list[dict]:
    base = _visible_ids_select(db, user)
    rows = db.query(Ticket.department, func.count(Ticket.id))\
        .filter(Ticket.id.in_(base), Ticket.department.isnot(None))\
        .group_by(Ticket.department).order_by(func.count(Ticket.id).desc()).all()
    return [{"department": r[0], "count": int(r[1])} for r in rows]


def monthly_trends(db: Session, user: User, months: int = 12) -> list[dict]:
    base = _visible_ids_select(db, user)
    now = _now()
    first = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    # Walk back to the first day of `months` months ago.
    y, m = first.year, first.month
    for _ in range(months - 1):
        m -= 1
        if m == 0:
            m = 12
            y -= 1
    since = now.replace(year=y, month=m, day=1, hour=0, minute=0, second=0, microsecond=0)
    rows = db.query(func.strftime("%Y-%m", Ticket.created_at).label("month"), func.count(Ticket.id))\
        .filter(Ticket.id.in_(base), Ticket.created_at >= since)\
        .group_by(func.strftime("%Y-%m", Ticket.created_at)).all()
    by_month = {str(r[0]): int(r[1]) for r in rows}

    out = []
    y, m = since.year, since.month
    for _ in range(months):
        key = f"{y:04d}-{m:02d}"
        out.append({"month": key, "count": by_month.get(key, 0)})
        m += 1
        if m == 13:
            m = 1
            y += 1
    return out


def sla_summary(db: Session, user: User) -> list[dict]:
    base = _visible_ids_select(db, user)
    counts = _keyed(db, base, Ticket.sla_status)
    return [{"status": s.value, "count": counts.get(s.value, 0)} for s in SlaStatus]


def breached_tickets(db: Session, user: User, limit: int = 10) -> list[dict]:
    base = _visible_ids_select(db, user)
    rows = db.query(Ticket.ticket_no, Ticket.title, Ticket.priority, Ticket.sla_deadline, Ticket.status)\
        .filter(Ticket.id.in_(base), Ticket.sla_status == SlaStatus.BREACHED.value)\
        .order_by(Ticket.sla_deadline.asc()).limit(limit).all()
    return [
        {
            "ticket_no": r[0], "title": r[1], "priority": r[2],
            "deadline": _utc_iso(r[3]), "status": r[4],
        }
        for r in rows
    ]