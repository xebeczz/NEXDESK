"""AI ticket drafts: persist recommendations, promote them only on confirmation.

The AI never creates a ticket directly. It produces a validated analysis; if the
backend rules say a ticket is warranted, a ``AiTicketDraft`` is persisted. A
user (or admin) explicitly confirms the draft before it becomes a real ticket.
"""
from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.enums import DraftStatus, NotificationType, TicketStatus, UserRole
from app.models.notification import AiTicketDraft
from app.models.ticket import Ticket
from app.models.user import User
from app.services import ticket_service as ts
from app.services.audit_service import log_action
from app.services.notification_service import create_notification


def create_draft(
    db: Session,
    user: User,
    chat_session_id: str,
    analysis: dict,
) -> AiTicketDraft:
    title = _draft_title(analysis)
    draft = AiTicketDraft(
        chat_session_id=chat_session_id,
        user_id=user.id,
        title=title,
        description=analysis.get("summary", ""),
        category=analysis.get("category", "General"),
        priority=analysis.get("priority", "medium"),
        department=analysis.get("department"),
        confidence=analysis.get("confidence", 0.5),
        intent=analysis.get("intent"),
        status=DraftStatus.PENDING,
    )
    db.add(draft)
    db.flush()
    # Notify admins about an AI recommendation.
    admins = (
        db.query(User)
        .filter(User.is_active.is_(True), User.role == UserRole.ADMIN)
        .all()
    )
    for u in admins:
        create_notification(
            db, u.id, NotificationType.AI_RECOMMENDATION.value,
            "AI ticket recommendation",
            f"{user.full_name} has an AI-proposed ticket: {title}",
            commit=False,
        )
    log_action(db, user.id, "ai.draft_created", "ai_ticket_draft", draft.id,
               {"title": title, "priority": draft.priority})
    db.commit()
    return draft


def get_draft_or_404(db: Session, draft_id: str, user: User) -> AiTicketDraft:
    draft = db.get(AiTicketDraft, draft_id)
    if draft is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Draft not found")
    if draft.user_id != user.id and user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your draft")
    return draft


def confirm_draft(db: Session, user: User, draft: AiTicketDraft) -> Ticket:
    if draft.status == DraftStatus.CREATED.value and draft.created_ticket_id:
        return db.get(Ticket, draft.created_ticket_id)
    ticket = Ticket(
        ticket_no=ts.next_ticket_no(db),
        title=draft.title,
        description=draft.description,
        category=draft.category,
        priority=draft.priority,
        status=TicketStatus.OPEN.value,
        department=draft.department,
        created_by_id=draft.user_id,
    )
    db.add(ticket)
    db.flush()
    ts.apply_sla(ticket)
    ts.log_activity(db, ticket, user or db.get(User, draft.user_id), "created",
                    new_value=f"via AI assistant ({draft.intent})")
    draft.status = DraftStatus.CREATED
    draft.created_ticket_id = ticket.id
    log_action(db, user.id, "ai.draft_confirmed", "ai_ticket_draft", draft.id, {"ticket_id": ticket.id})
    db.commit()
    return ticket


def _draft_title(analysis: dict) -> str:
    intent = analysis.get("intent", "")
    intent_label = intent.replace("_", " ").title()
    return f"[AI] {intent_label}: {analysis.get('category', 'General')} issue"