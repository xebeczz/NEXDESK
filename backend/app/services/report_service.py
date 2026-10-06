"""PDF report generation with ReportLab.

Every report is rendered from live, role-scoped SQL aggregates computed in
``analytics_service`` — no hardcoded figures. Reports stream as PDF bytes back
to the client for download.
"""
from __future__ import annotations

from datetime import datetime, timezone
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.ticket import Ticket
from app.models.user import User
from app.services import analytics_service as analytics

_HEADER_BG = colors.HexColor("#4f46e5")
_ALT_ROW = colors.HexColor("#f4f4f5")
_BORDER = colors.HexColor("#e4e4e7")


def _now_label() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def _styles():
    styles = getSampleStyleSheet()
    title = styles["Title"]
    title.textColor = _HEADER_BG
    title.fontSize = 18
    styles.add(
        ParagraphStyle(
            "H2",
            parent=styles["Heading2"],
            spaceBefore=10,
            spaceAfter=4,
            textColor=colors.HexColor("#27272a"),
        )
    )
    return styles


def _kv_table(rows: list[tuple[str, str | int | None]]) -> Table:
    data = [[Paragraph("<b>Metric</b>"), Paragraph("<b>Value</b>")]] + [
        [Paragraph(str(k)), Paragraph(str(v) if v is not None else "—")] for k, v in rows
    ]
    table = Table(data, colWidths=[70 * mm, 80 * mm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), _HEADER_BG),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, _ALT_ROW]),
                ("GRID", (0, 0), (-1, -1), 0.4, _BORDER),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return table


def _data_table(header: list[str], rows: list[list[str]]) -> Table:
    data = [[Paragraph(f"<b>{c}</b>") for c in header]] + [[Paragraph(str(c)) for c in row] for row in rows]
    table = Table(data, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), _HEADER_BG),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, _ALT_ROW]),
                ("GRID", (0, 0), (-1, -1), 0.4, _BORDER),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return table


def _render(title: str, subtitle: str, elements) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
        title=title,
        author=settings.APP_NAME,
    )
    styles = _styles()
    story = [
        Paragraph(title, styles["Title"]),
        Paragraph(subtitle, styles["Normal"]),
        Spacer(1, 6 * mm),
        Paragraph(f"Generated: {_now_label()}", styles["Normal"]),
        Spacer(1, 6 * mm),
    ]
    story.extend(elements)
    doc.build(story)
    return buffer.getvalue()


def _pct_part(total: int, count: int) -> str:
    return f"{round(count / total * 100, 1)}%" if total else "—"


def build_summary(db: Session, user: User) -> bytes:
    s = analytics.dashboard_stats(db, user)
    total = s["total"]
    elements = [
        _kv_table(
            [
                ("Total tickets", s["total"]),
                ("Open", s["open"]),
                ("In progress", s["in_progress"]),
                ("Pending", s["pending"]),
                ("Resolved", s["resolved"]),
                ("Closed", s["closed"]),
                ("High priority", s["high_priority"]),
                ("Critical", s["critical"]),
                ("SLA compliance", f'{s["sla_compliance_percent"]}%' if s["sla_compliance_percent"] is not None else "—"),
                ("SLA breached", s["sla_breached"]),
                ("Avg resolution (hours)", s["avg_resolution_hours"]),
                ("Tickets today / week / month", f'{s["tickets_today"]} / {s["tickets_this_week"]} / {s["tickets_this_month"]}'),
                ("Top department", s["top_department"]),
            ]
        ),
        Spacer(1, 4 * mm),
        Paragraph("Status breakdown", _styles()["H2"]),
        _data_table(
            ["Status", "Count", "Share"],
            [
                [k.replace("_", " ").title(), str(v), _pct_part(total, v)]
                for k, v in s["status_counts"].items()
            ],
        ),
        Spacer(1, 4 * mm),
        Paragraph("Priority breakdown", _styles()["H2"]),
        _data_table(
            ["Priority", "Count", "Share"],
            [
                [k.title(), str(v), _pct_part(total, v)]
                for k, v in s["priority_counts"].items()
            ],
        ),
    ]
    return _render("Ticket Summary Report", settings.APP_NAME, elements)


def build_analytics(db: Session, user: User) -> bytes:
    dept = analytics.department_distribution(db, user)
    sla = analytics.sla_summary(db, user)
    s = analytics.dashboard_stats(db, user)
    elements = [
        Paragraph("Department distribution", _styles()["H2"]),
        _data_table(
            ["Department", "Count"],
            [[d["department"] or "Unspecified", str(d["count"])] for d in dept],
        ),
        Spacer(1, 4 * mm),
        Paragraph("SLA status", _styles()["H2"]),
        _data_table(
            ["Status", "Count"],
            [[x["status"].replace("_", " ").title(), str(x["count"])] for x in sla],
        ),
        Spacer(1, 4 * mm),
        Paragraph("Key figures", _styles()["H2"]),
        _kv_table(
            [
                ("Active tickets", s["active"]),
                ("Unresolved", s["unresolved"]),
                ("SLA compliance", f'{s["sla_compliance_percent"]}%' if s["sla_compliance_percent"] is not None else "—"),
                ("Breached", s["sla_breached"]),
            ]
        ),
    ]
    return _render("Analytics Overview Report", settings.APP_NAME, elements)


def build_resolution(db: Session, user: User) -> bytes:
    s = analytics.dashboard_stats(db, user)
    breached = analytics.breached_tickets(db, user, limit=20)
    elements = [
        _kv_table(
            [
                ("Average resolution (hours)", s["avg_resolution_hours"]),
                ("Resolved", s["resolved"]),
                ("SLA compliance", f'{s["sla_compliance_percent"]}%' if s["sla_compliance_percent"] is not None else "—"),
                ("Breached tickets", s["sla_breached"]),
                ("At risk (warning)", s["sla_warning"]),
            ]
        ),
        Spacer(1, 4 * mm),
        Paragraph("Breached tickets", _styles()["H2"]),
        _data_table(
            ["Ticket", "Priority", "Deadline", "Status"],
            [
                [b["ticket_no"], b["priority"], b["deadline"] or "—", b["status"].replace("_", " ").title()]
                for b in breached
            ],
        ),
    ]
    return _render("Resolution Times Report", settings.APP_NAME, elements)


def build_priority(db: Session, user: User) -> bytes:
    dist = analytics.priority_distribution(db, user)
    s = analytics.dashboard_stats(db, user)
    total = s["total"]
    elements = [
        Paragraph("Tickets by priority", _styles()["H2"]),
        _data_table(
            ["Priority", "Count", "Share"],
            [
                [d["priority"].title(), str(d["count"]), _pct_part(total, d["count"])]
                for d in dist
            ],
        ),
        Spacer(1, 4 * mm),
        _kv_table(
            [
                ("High priority", s["high_priority"]),
                ("Critical", s["critical"]),
                ("Active (high/critical)", s["high_priority"] + s["critical"]),
            ]
        ),
    ]
    return _render("Priority Analysis Report", settings.APP_NAME, elements)


def build_monthly(db: Session, user: User) -> bytes:
    trend = analytics.monthly_trends(db, user, months=12)
    elements = [
        Paragraph("Monthly ticket creation (last 12 months)", _styles()["H2"]),
        _data_table(
            ["Month", "Tickets created"],
            [[t["month"], str(t["count"])] for t in trend],
        ),
    ]
    return _render("Monthly Trends Report", settings.APP_NAME, elements)


def build_ticket_pdf(ticket: Ticket) -> bytes:
    elements = [
        _kv_table(
            [
                ("Ticket", ticket.ticket_no),
                ("Title", ticket.title),
                ("Status", ticket.status.replace("_", " ").title()),
                ("Priority", ticket.priority.title()),
                ("Category", ticket.category),
                ("Department", ticket.department or "—"),
                ("Created", _fmt_dt(ticket.created_at)),
                ("SLA deadline", _fmt_dt(ticket.sla_deadline)),
            ]
        ),
        Spacer(1, 4 * mm),
        Paragraph("Description", _styles()["H2"]),
        Paragraph(ticket.description or "—", _styles()["Normal"]),
    ]
    if ticket.resolution_notes:
        elements += [Spacer(1, 4 * mm), Paragraph("Resolution notes", _styles()["H2"]), Paragraph(ticket.resolution_notes, _styles()["Normal"])]
    return _render(f"Ticket {ticket.ticket_no}", settings.APP_NAME, elements)


def _fmt_dt(dt) -> str:
    if dt is None:
        return "—"
    return dt.strftime("%Y-%m-%d %H:%M")