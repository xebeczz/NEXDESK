"""Admin platform endpoints: user management, workload, system health, audit."""
from __future__ import annotations

import time
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.deps import require_admin
from app.core.security import hash_password
from app.db.session import get_db
from app.models.audit_log import AuditLog
from app.models.enums import DraftStatus, TicketStatus
from app.models.notification import AiTicketDraft
from app.models.ticket import Ticket
from app.models.user import User
from app.schemas import admin as admin_schema
from app.schemas.user import UserCreate, UserRead, UserUpdate
from app.services.audit_service import log_action
from app.services.notification_service import create_notification

router = APIRouter(prefix="/admin", tags=["admin"])

# Rough uptime reference — set when this module first loads (server start).
_SERVER_START = datetime.now()


# --- User management ---
@router.get("/users", response_model=list[UserRead])
def list_users(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    return db.query(User).order_by(User.created_at.desc()).all()


@router.post("/users", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    if db.query(User).filter(User.email == payload.email).one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    if db.query(User).filter(User.username == payload.username).one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already taken")
    user = User(
        email=payload.email,
        username=payload.username,
        full_name=payload.full_name,
        department=payload.department,
        role=UserRole.USER,  # admin-created users default to employee; elevate via PATCH
        hashed_password=hash_password(payload.password),
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    log_action(db, admin.id, "admin.user_created", "user", user.id,
               {"email": user.email, "role": str(user.role)})
    create_notification(db, user.id, "login_success", "Account created",
                        f"Welcome {user.full_name}. Your account has been set up by an administrator.",
                        commit=True)
    return user


@router.patch("/users/{user_id}", response_model=UserRead)
def update_user(user_id: str, payload: UserUpdate, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    changes = {}
    if payload.full_name:
        user.full_name = payload.full_name
        changes["full_name"] = payload.full_name
    if payload.department is not None:
        user.department = payload.department
        changes["department"] = payload.department
    if payload.role is not None:
        user.role = payload.role
        changes["role"] = payload.role.value
    if payload.is_active is not None:
        user.is_active = payload.is_active
        changes["is_active"] = payload.is_active
    db.commit()
    db.refresh(user)
    log_action(db, admin.id, "user.updated", "user", user.id, changes)
    return user


# --- System health ---
@router.get("/system-health", response_model=admin_schema.SystemHealth)
def system_health(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    start = time.perf_counter()
    try:
        db.execute(select(1))
        db_status = "ok"
    except Exception:  # NOQA: BLE001
        db_status = "error"
    query_ms = round((time.perf_counter() - start) * 1000, 2) if db_status == "ok" else None

    total_users = db.query(func.count(User.id)).scalar() or 0
    total_tickets = db.query(func.count(Ticket.id)).scalar() or 0
    active_tickets = db.query(func.count(Ticket.id)).filter(Ticket.status.in_([
        TicketStatus.OPEN.value, TicketStatus.IN_PROGRESS.value, TicketStatus.PENDING.value])).scalar() or 0
    pending_drafts = db.query(func.count(AiTicketDraft.id)).filter(
        AiTicketDraft.status == DraftStatus.PENDING.value).scalar() or 0

    uptime = (datetime.now() - _SERVER_START).total_seconds()

    return admin_schema.SystemHealth(
        status="ok" if db_status == "ok" else "degraded",
        uptime_seconds=uptime,
        environment=settings.APP_ENV,
        db_status=db_status,
        db_query_ms=query_ms,
        total_users=total_users,
        total_tickets=total_tickets,
        active_tickets=active_tickets,
        pending_drafts=pending_drafts,
    )


# --- Audit log ---
@router.get("/audit-logs", response_model=admin_schema.AuditListResponse)
def audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(30, ge=1, le=100),
    action: str | None = Query(default=None, max_length=60),
    user_id: str | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    q = db.query(AuditLog)
    if action:
        q = q.filter(AuditLog.action.like(f"%{action}%"))
    if user_id:
        q = q.filter(AuditLog.user_id == user_id)
    total = q.count()
    rows = q.order_by(AuditLog.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    items = []
    for row in rows:
        actor = None
        if row.user_id:
            actor_user = db.get(User, row.user_id)
            actor = actor_user.full_name if actor_user else None
        items.append({
            "id": row.id,
            "actor": actor,
            "action": row.action,
            "entity_type": row.entity_type,
            "entity_id": row.entity_id,
            "details": row.details,
            "created_at": row.created_at,
        })
    pages = (total + page_size - 1) // page_size
    return admin_schema.AuditListResponse(items=items, total=total, page=page, page_size=page_size, pages=pages)