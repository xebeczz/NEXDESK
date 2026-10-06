"""Dashboard KPI endpoint — real aggregates, role-scoped."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas import dashboard as dash_schema
from app.services.analytics_service import dashboard_stats

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=dash_schema.DashboardStats)
def stats(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return dashboard_stats(db, user)