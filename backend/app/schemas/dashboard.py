"""Response schemas for dashboard KPIs and analytics chart data."""
from __future__ import annotations

from pydantic import BaseModel


class DashboardStats(BaseModel):
    total: int
    open: int
    in_progress: int
    pending: int
    resolved: int
    closed: int
    active: int
    unresolved: int
    high_priority: int
    critical: int
    avg_resolution_hours: float | None = None
    sla_compliance_percent: float | None = None
    sla_breached: int = 0
    sla_warning: int = 0
    tickets_today: int = 0
    tickets_this_week: int = 0
    tickets_this_month: int = 0
    top_department: str | None = None
    status_counts: dict[str, int] = {}
    priority_counts: dict[str, int] = {}
    sla_counts: dict[str, int] = {}


class TimePoint(BaseModel):
    date: str
    count: int


class MonthPoint(BaseModel):
    month: str
    count: int


class PriorityPoint(BaseModel):
    priority: str
    count: int


class StatusPoint(BaseModel):
    status: str
    count: int


class DepartmentPoint(BaseModel):
    department: str
    count: int


class SlaPoint(BaseModel):
    status: str
    count: int


class BreachedTicket(BaseModel):
    ticket_no: str
    title: str
    priority: str
    deadline: str | None = None
    status: str


class TrendResponse(BaseModel):
    items: list[TimePoint]


class MonthlyResponse(BaseModel):
    items: list[MonthPoint]


class DistributionResponse(BaseModel):
    items: list


class SlaResponse(BaseModel):
    items: list[SlaPoint]


class BreachedResponse(BaseModel):
    items: list[BreachedTicket]