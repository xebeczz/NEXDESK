"""Ticket management endpoints: CRUD, search, assign/transfer, status, comments, attachments."""
from __future__ import annotations

import os
import secrets as _secrets

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse, Response
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.core.config import settings
from app.core.deps import get_current_user, require_admin
from app.db.base import utcnow
from app.db.session import get_db
from app.models.enums import NotificationType, TicketStatus, UserRole
from app.models.ticket import Ticket, TicketActivity, TicketAttachment, TicketComment
from app.models.user import User
from app.schemas import ticket as ticket_schema
from app.schemas.common import MessageResponse
from app.services.audit_service import log_action
from app.services.notification_service import create_notification
from app.services import ticket_service as ts

router = APIRouter(prefix="/tickets", tags=["tickets"])

ALLOWED_CONTENT_TYPES = {
    "image/png", "image/jpeg", "image/gif", "image/webp", "image/svg+xml",
    "application/pdf", "text/plain", "application/zip", "application/x-zip-compressed",
    "text/x-log", "application/octet-stream",
}
MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB


def _get_ticket_or_404(db: Session, ticket_id: str) -> Ticket:
    ticket = db.get(Ticket, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    return ticket


def _load_detail(db: Session, ticket_id: str) -> Ticket:
    return (
        db.query(Ticket)
        .options(
            joinedload(Ticket.comments).joinedload(TicketComment.user),
            joinedload(Ticket.activities).joinedload(TicketActivity.user),
            joinedload(Ticket.attachments).joinedload(TicketAttachment.uploader),
            joinedload(Ticket.created_by),
            joinedload(Ticket.assigned_to),
        )
        .filter(Ticket.id == ticket_id)
        .one_or_none()
    )


def _resolve_detail(db: Session, ticket_id: str):
    ticket = _load_detail(db, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    return ts.build_detail(ticket)


def _require_view(user: User, ticket: Ticket) -> None:
    if not ts.can_view(user, ticket):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You cannot view this ticket")


def _require_manage(user: User, ticket: Ticket) -> None:
    if not ts.can_manage(user, ticket):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You cannot modify this ticket")


def _notify(db: Session, user_ids: list[str], type_: str, title: str, message: str, ticket_id: str | None = None):
    for uid in user_ids:
        create_notification(db, uid, type_, title, message, ticket_id, commit=False)


def _targets_for(actor: User, ticket: Ticket) -> list[str]:
    """Creator + assignee, excluding the acting user."""
    targets = []
    if ticket.created_by_id and ticket.created_by_id != actor.id:
        targets.append(ticket.created_by_id)
    if ticket.assigned_to_id and ticket.assigned_to_id != actor.id:
        targets.append(ticket.assigned_to_id)
    return targets


def _admin_notify(db: Session, ticket: Ticket) -> None:
    """Notify admins in the ticket's department on creation."""
    q = db.query(User).filter(User.is_active.is_(True), User.role == UserRole.ADMIN)
    if ticket.department:
        q = q.filter(or_(User.department == ticket.department, User.role == UserRole.ADMIN))
    ids = [u.id for u in q.all()]
    if ticket.assigned_to_id and ticket.assigned_to_id not in ids:
        ids.append(ticket.assigned_to_id)
    _notify(db, ids, NotificationType.TICKET_CREATED.value, "New ticket",
            f"New ticket {ticket.ticket_no}: {ticket.title}", ticket.id)


def _str(value) -> str | None:
    return str(value) if value is not None else None


@router.get("", response_model=ticket_schema.TicketListResponse)
def list_tickets(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = Query(default=None, max_length=255),
    category: str | None = Query(default=None, max_length=80),
    priority: str | None = None,
    status_: str | None = Query(default=None, alias="status"),
    department: str | None = Query(default=None, max_length=120),
    created_by: str | None = None,
    assigned_to: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    sort_by: str = Query(default="created_at", pattern="^(created_at|updated_at|priority|status|title)$"),
    sort_order: str = Query(default="desc", pattern="^(asc|desc)$"),
):
    q = ts.user_visible_query(db, user)
    if search:
        like = f"%{search}%"
        q = q.filter(or_(Ticket.title.like(like), Ticket.ticket_no.like(like), Ticket.description.like(like)))
    if category:
        q = q.filter(Ticket.category == category)
    if priority:
        q = q.filter(Ticket.priority == priority)
    if status_:
        q = q.filter(Ticket.status == status_)
    if department:
        q = q.filter(Ticket.department == department)
    if created_by:
        q = q.filter(Ticket.created_by_id == created_by)
    if assigned_to:
        q = q.filter(Ticket.assigned_to_id == assigned_to)
    if date_from:
        q = q.filter(Ticket.created_at >= f"{date_from}T00:00:00")
    if date_to:
        q = q.filter(Ticket.created_at <= f"{date_to}T23:59:59")

    column = {
        "created_at": Ticket.created_at,
        "updated_at": Ticket.updated_at,
        "priority": Ticket.priority,
        "status": Ticket.status,
        "title": Ticket.title,
    }[sort_by]
    q = q.order_by(column.desc() if sort_order == "desc" else column.asc())

    total = q.count()
    items = (
        q.options(joinedload(Ticket.created_by), joinedload(Ticket.assigned_to))
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    pages = (total + page_size - 1) // page_size
    return ticket_schema.TicketListResponse(
        items=[ticket_schema.TicketRead.model_validate(t) for t in items],
        total=total, page=page, page_size=page_size, pages=pages,
    )


@router.post("", response_model=ticket_schema.TicketDetail, status_code=status.HTTP_201_CREATED)
def create_ticket(
    payload: ticket_schema.TicketCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if payload.assigned_to_id and user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can assign a ticket at creation")
    print(f"[DEBUG] create_ticket payload: title={payload.title!r}, category={payload.category!r}, priority={payload.priority!r}, department={payload.department!r}")
    ticket = Ticket(
        ticket_no=ts.next_ticket_no(db),
        title=payload.title,
        description=payload.description,
        category=payload.category,
        priority=payload.priority,
        status=TicketStatus.OPEN.value,
        department=payload.department or user.department,
        created_by_id=user.id,
        assigned_to_id=payload.assigned_to_id,
        similar_ticket_ids=",".join(payload.similar_ticket_ids) if payload.similar_ticket_ids else None,
    )
    db.add(ticket)
    db.flush()
    ts.apply_sla(ticket)
    ts.log_activity(db, ticket, user, "created")
    log_action(db, user.id, "ticket.create", "ticket", ticket.id, {"ticket_no": ticket.ticket_no})
    _admin_notify(db, ticket)
    db.commit()
    print(f"[DEBUG] create_ticket success: id={ticket.id}, ticket_no={ticket.ticket_no}")
    return _resolve_detail(db, ticket.id)


@router.post("/similar", response_model=ticket_schema.SimilarTicketsResponse)
def find_similar_tickets(
    payload: dict,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    from app.services.similar_tickets import find_similar_tickets as search_similar

    title = str(payload.get("title", "")).strip()
    description = str(payload.get("description", "")).strip()
    category = payload.get("category")
    priority = payload.get("priority")
    department = payload.get("department")
    exclude_ticket_id = payload.get("exclude_ticket_id")
    threshold = float(payload.get("threshold", 70.0))
    limit = int(payload.get("limit", 5))

    if not title and not description:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="title or description is required")

    results = search_similar(
        db,
        current_title=title,
        current_description=description,
        current_category=category,
        current_priority=priority,
        current_department=department,
        threshold=threshold,
        limit=limit,
        exclude_ticket_id=exclude_ticket_id,
    )
    return ticket_schema.SimilarTicketsResponse(similar_tickets=[ticket_schema.SimilarTicket(**r) for r in results])


@router.get("/{ticket_id}", response_model=ticket_schema.TicketDetail)
def get_ticket(ticket_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    ticket = _get_ticket_or_404(db, ticket_id)
    _require_view(user, ticket)
    ts.apply_sla(ticket)
    db.commit()
    return _resolve_detail(db, ticket.id)


@router.put("/{ticket_id}", response_model=ticket_schema.TicketDetail)
def update_ticket(
    ticket_id: str,
    payload: ticket_schema.TicketUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    ticket = _get_ticket_or_404(db, ticket_id)
    _require_manage(user, ticket)
    changes: list[tuple] = []
    for field_name in ("title", "description", "category", "priority", "department", "resolution_notes", "status"):
        value = getattr(payload, field_name, None)
        if value is not None:
            old = getattr(ticket, field_name)
            if old != value:
                setattr(ticket, field_name, value)
                changes.append((field_name, old, value))
    if ticket.status == TicketStatus.RESOLVED.value and ticket.resolved_at is None:
        ticket.resolved_at = utcnow()
    if ticket.status == TicketStatus.CLOSED.value and ticket.closed_at is None:
        ticket.closed_at = utcnow()
    ts.apply_sla(ticket)
    for field, old, new in changes:
        ts.log_activity(db, ticket, user, "updated", field=field, old_value=_str(old), new_value=_str(new))
    if changes:
        log_action(db, user.id, "ticket.update", "ticket", ticket.id,
                   {f: _str(v) for f, _, v in changes})
        _notify(db, _targets_for(user, ticket), NotificationType.TICKET_UPDATED.value,
                "Ticket updated", f"{ticket.ticket_no} was updated", ticket.id)
    db.commit()
    return _resolve_detail(db, ticket.id)


@router.post("/{ticket_id}/status", response_model=ticket_schema.TicketDetail)
def change_status(
    ticket_id: str,
    payload: ticket_schema.StatusChangeRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    ticket = _get_ticket_or_404(db, ticket_id)
    _require_manage(user, ticket)
    new_status = payload.status.value
    resolution_notes = payload.resolution_notes
    if new_status not in {s.value for s in TicketStatus}:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid status")
    old = ticket.status
    ticket.status = new_status
    if new_status in (TicketStatus.RESOLVED.value, TicketStatus.CLOSED.value):
        if new_status == TicketStatus.RESOLVED.value:
            ticket.resolved_at = ticket.resolved_at or utcnow()
        else:
            ticket.closed_at = ticket.closed_at or utcnow()
        if resolution_notes:
            ticket.resolution_notes = resolution_notes
    ts.log_activity(db, ticket, user, "status_changed", field="status", old_value=old, new_value=new_status)
    log_action(db, user.id, "ticket.status_change", "ticket", ticket.id, {"from": old, "to": new_status})
    _notify(db, _targets_for(user, ticket), NotificationType.TICKET_UPDATED.value,
            "Ticket status updated", f"{ticket.ticket_no} \u2192 {new_status}", ticket.id)
    db.commit()
    return _resolve_detail(db, ticket.id)


@router.post("/{ticket_id}/close", response_model=ticket_schema.TicketDetail)
def close_ticket(
    ticket_id: str,
    payload: ticket_schema.CloseRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    ticket = _get_ticket_or_404(db, ticket_id)
    _require_manage(user, ticket)
    old = ticket.status
    ticket.status = TicketStatus.CLOSED.value
    ticket.closed_at = utcnow()
    if payload.resolution_notes:
        ticket.resolution_notes = payload.resolution_notes
    ts.log_activity(db, ticket, user, "closed", field="status", old_value=old, new_value=TicketStatus.CLOSED.value)
    _notify(db, _targets_for(user, ticket), NotificationType.TICKET_CLOSED.value,
            "Ticket closed", f"{ticket.ticket_no} was closed", ticket.id)
    log_action(db, user.id, "ticket.close", "ticket", ticket.id)
    db.commit()
    return _resolve_detail(db, ticket.id)


@router.post("/{ticket_id}/reopen", response_model=ticket_schema.TicketDetail)
def reopen_ticket(ticket_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    ticket = _get_ticket_or_404(db, ticket_id)
    _require_manage(user, ticket)
    old = ticket.status
    ticket.status = TicketStatus.OPEN.value
    ticket.resolved_at = None
    ticket.closed_at = None
    ts.log_activity(db, ticket, user, "reopened", field="status", old_value=old, new_value=TicketStatus.OPEN.value)
    _notify(db, _targets_for(user, ticket), NotificationType.TICKET_UPDATED.value,
            "Ticket reopened", f"{ticket.ticket_no} was reopened", ticket.id)
    log_action(db, user.id, "ticket.reopen", "ticket", ticket.id)
    db.commit()
    return _resolve_detail(db, ticket.id)


@router.post("/{ticket_id}/assign", response_model=ticket_schema.TicketDetail)
def assign_ticket(
    ticket_id: str,
    payload: ticket_schema.AssignRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    ticket = _get_ticket_or_404(db, ticket_id)
    if user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can assign tickets")
    assignee = db.get(User, payload.assigned_to_id)
    if assignee is None or assignee.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Assignee must be an admin")
    old = ticket.assigned_to_id
    ticket.assigned_to = assignee
    ts.log_activity(db, ticket, user, "assigned", field="assigned_to_id", old_value=old, new_value=assignee.id)
    create_notification(db, assignee.id, NotificationType.TICKET_ASSIGNED.value,
                        "Ticket assigned to you", f"{ticket.ticket_no}: {ticket.title}", ticket.id, commit=False)
    _notify(db, _targets_for(user, ticket), NotificationType.TICKET_ASSIGNED.value,
            "Ticket assigned", f"{ticket.ticket_no} assigned to {assignee.full_name}", ticket.id)
    log_action(db, user.id, "ticket.assign", "ticket", ticket.id, {"assignee": assignee.id})
    db.commit()
    return _resolve_detail(db, ticket.id)


@router.post("/{ticket_id}/transfer", response_model=ticket_schema.TicketDetail)
def transfer_ticket(
    ticket_id: str,
    payload: ticket_schema.AssignRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    ticket = _get_ticket_or_404(db, ticket_id)
    if user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can transfer tickets")
    assignee = db.get(User, payload.assigned_to_id)
    if assignee is None or assignee.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Target assignee must be an admin")
    old = ticket.assigned_to_id
    ticket.assigned_to = assignee
    ts.log_activity(db, ticket, user, "transferred", field="assigned_to_id", old_value=old, new_value=assignee.id)
    create_notification(db, assignee.id, NotificationType.TICKET_ASSIGNED.value,
                        "Ticket transferred to you", f"{ticket.ticket_no}: {ticket.title}", ticket.id, commit=False)
    log_action(db, user.id, "ticket.transfer", "ticket", ticket.id, {"from": old, "to": assignee.id})
    db.commit()
    return _resolve_detail(db, ticket.id)


@router.delete("/{ticket_id}", response_model=MessageResponse)
def delete_ticket(
    ticket_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    ticket = _get_ticket_or_404(db, ticket_id)
    log_action(db, user.id, "ticket.delete", "ticket", ticket.id, {"ticket_no": ticket.ticket_no})
    db.delete(ticket)
    db.commit()
    return MessageResponse(message="Ticket deleted")


# --- Comments ---
@router.get("/{ticket_id}/activities", response_model=list[ticket_schema.TicketActivityRead])
def list_activities(ticket_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    ticket = _get_ticket_or_404(db, ticket_id)
    _require_view(user, ticket)
    items = (
        db.query(TicketActivity)
        .options(joinedload(TicketActivity.user))
        .filter(TicketActivity.ticket_id == ticket.id)
        .order_by(TicketActivity.created_at)
        .all()
    )
    out: list[dict] = []
    for a in items:
        item = ticket_schema.TicketActivityRead.model_validate(a).model_dump()
        item["user"] = None if not a.user else {
            "id": a.user.id, "username": a.user.username, "full_name": a.user.full_name,
            "email": a.user.email, "role": a.user.role, "department": a.user.department}
        out.append(item)
    return out


@router.get("/{ticket_id}/comments", response_model=list[ticket_schema.TicketCommentRead])
def list_comments(ticket_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    ticket = _get_ticket_or_404(db, ticket_id)
    _require_view(user, ticket)
    return ticket.comments


@router.post("/{ticket_id}/comments", response_model=ticket_schema.TicketCommentRead, status_code=status.HTTP_201_CREATED)
def add_comment(
    ticket_id: str,
    payload: ticket_schema.TicketCommentCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    ticket = _get_ticket_or_404(db, ticket_id)
    _require_view(user, ticket)
    comment = TicketComment(ticket_id=ticket.id, user_id=user.id, content=payload.content)
    db.add(comment)
    db.flush()
    ts.log_activity(db, ticket, user, "commented", field="comment", new_value=payload.content[:200])
    _notify(db, _targets_for(user, ticket), NotificationType.TICKET_COMMENTED.value,
            "New comment", f"{user.full_name} commented on {ticket.ticket_no}", ticket.id)
    db.commit()
    return (
        db.query(TicketComment)
        .options(joinedload(TicketComment.user))
        .filter(TicketComment.id == comment.id)
        .first()
    )


# --- Attachments ---
@router.post("/{ticket_id}/attachments", response_model=ticket_schema.TicketAttachmentRead, status_code=status.HTTP_201_CREATED)
def upload_attachment(
    ticket_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    ticket = _get_ticket_or_404(db, ticket_id)
    _require_view(user, ticket)
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                            detail=f"File type '{file.content_type}' not allowed")
    data = file.file.read()
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="File exceeds 10 MB limit")

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    safe_name = os.path.basename(file.filename or "file")
    stored_filename = f"{_secrets.token_hex(16)}_{safe_name}"
    with open(os.path.join(settings.UPLOAD_DIR, stored_filename), "wb") as fh:
        fh.write(data)

    attachment = TicketAttachment(
        ticket_id=ticket.id,
        uploader_id=user.id,
        filename=safe_name,
        stored_filename=stored_filename,
        size=len(data),
        content_type=file.content_type,
    )
    db.add(attachment)
    db.flush()
    ts.log_activity(db, ticket, user, "attachment_added", field="attachment", new_value=safe_name)
    log_action(db, user.id, "ticket.attach", "ticket", ticket.id, {"filename": safe_name})
    db.commit()
    result = ticket_schema.TicketAttachmentRead.model_validate(attachment).model_dump()
    result["uploaded_by"] = {"id": user.id, "username": user.username, "full_name": user.full_name,
                             "email": user.email, "role": user.role, "department": user.department}
    return result


@router.get("/{ticket_id}/attachments", response_model=list[ticket_schema.TicketAttachmentRead])
def list_attachments(ticket_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    ticket = _get_ticket_or_404(db, ticket_id)
    _require_view(user, ticket)
    out: list[dict] = []
    for a in ticket.attachments:
        item = ticket_schema.TicketAttachmentRead.model_validate(a).model_dump()
        item["uploaded_by"] = None if not a.uploader else {
            "id": a.uploader.id, "username": a.uploader.username, "full_name": a.uploader.full_name,
            "email": a.uploader.email, "role": a.uploader.role, "department": a.uploader.department}
        out.append(item)
    return out


@router.get("/{ticket_id}/attachments/{attachment_id}/download")
def download_attachment(
    ticket_id: str,
    attachment_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    ticket = _get_ticket_or_404(db, ticket_id)
    _require_view(user, ticket)
    attachment = db.get(TicketAttachment, attachment_id)
    if attachment is None or attachment.ticket_id != ticket.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attachment not found")
    path = os.path.join(settings.UPLOAD_DIR, attachment.stored_filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attachment file missing")
    return FileResponse(path, media_type=attachment.content_type, filename=attachment.filename)


@router.get("/{ticket_id}/pdf")
def ticket_pdf(
    ticket_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Stream a PDF document for a single ticket."""
    ticket = _get_ticket_or_404(db, ticket_id)
    _require_view(user, ticket)
    from app.services import report_service

    pdf = report_service.build_ticket_pdf(ticket)
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{ticket.ticket_no}.pdf"'
        },
    )