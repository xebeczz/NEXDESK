"""Analytics chart endpoints — real SQL aggregates, role-scoped."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas import dashboard as dash_schema
from app.services import analytics_service as an

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/tickets-over-time", response_model=dash_schema.TrendResponse)
def tickets_over_time(
    days: int = Query(default=30, ge=7, le=365),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return {"items": an.tickets_over_time(db, user, days)}


@router.get("/monthly-trends", response_model=dash_schema.MonthlyResponse)
def monthly_trends(
    months: int = Query(default=12, ge=3, le=36),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return {"items": an.monthly_trends(db, user, months)}


@router.get("/priority-distribution", response_model=dash_schema.DistributionResponse)
def priority_distribution(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return {"items": an.priority_distribution(db, user)}


@router.get("/status-distribution", response_model=dash_schema.DistributionResponse)
def status_distribution(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return {"items": an.status_distribution(db, user)}


@router.get("/department-distribution", response_model=dash_schema.DistributionResponse)
def department_distribution(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return {"items": an.department_distribution(db, user)}


@router.get("/sla", response_model=dash_schema.SlaResponse)
def sla_summary(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return {"items": an.sla_summary(db, user)}


@router.get("/sla-breached", response_model=dash_schema.BreachedResponse)
def sla_breached(
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return {"items": an.breached_tickets(db, user, limit)}