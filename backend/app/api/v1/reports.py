"""PDF report endpoints.

Generates real PDF documents from admin-scoped SQL aggregates. Access is limited
to admin role.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_admin
from app.db.session import get_db
from app.models.user import User
from app.services import report_service

router = APIRouter(prefix="/reports", tags=["reports"])

_BUILDERS = {
    "summary": report_service.build_summary,
    "analytics": report_service.build_analytics,
    "resolution": report_service.build_resolution,
    "priority": report_service.build_priority,
    "monthly": report_service.build_monthly,
}


@router.get("/{report_type}")
def get_report(
    report_type: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    builder = _BUILDERS.get(report_type)
    if builder is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unknown report type",
        )
    pdf = builder(db, user)
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="itdesk-{report_type}-report.pdf"'
        },
    )