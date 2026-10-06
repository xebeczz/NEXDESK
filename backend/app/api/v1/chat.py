"""AI chat endpoints: sessions, streaming messages (SSE), and ticket-draft control."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.chat import ChatMessage, ChatSession
from app.models.enums import DraftStatus
from app.models.notification import AiTicketDraft
from app.models.user import User
from app.schemas import chat as chat_schema
from app.schemas.common import MessageResponse
from app.services import ai_rules, ai_ticket
from app.services.ai_service import ai_service
from app.services.notification_service import create_notification

router = APIRouter(prefix="/chat", tags=["chat"])


def _now_naive():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _sse(event: dict) -> str:
    return f"data: {json.dumps(event)}\n\n"


def _get_session_or_404(db: Session, session_id: str, user: User) -> ChatSession:
    session = db.get(ChatSession, session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat session not found")
    if session.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your chat session")
    return session


# --- Sessions ---
@router.get("/sessions", response_model=list[chat_schema.ChatSessionRead])
def list_sessions(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = (
        db.query(ChatSession, func.count(ChatMessage.id))
        .outerjoin(ChatMessage, ChatMessage.session_id == ChatSession.id)
        .filter(ChatSession.user_id == user.id)
        .group_by(ChatSession.id)
        .order_by(ChatSession.updated_at.desc())
        .all()
    )
    out = []
    for session, count in rows:
        item = chat_schema.ChatSessionRead.model_validate(session)
        out.append(item.model_copy(update={"message_count": count}))
    return out


@router.post("/sessions", response_model=chat_schema.ChatSessionRead, status_code=status.HTTP_201_CREATED)
def create_session(
    payload: chat_schema.ChatSessionCreate | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    session = ChatSession(user_id=user.id, title=(payload.title if payload else None) or "New conversation")
    db.add(session)
    db.commit()
    return chat_schema.ChatSessionRead.model_validate(session)


@router.get("/sessions/{session_id}/messages", response_model=list[chat_schema.ChatMessageRead])
def list_messages(session_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    session = _get_session_or_404(db, session_id, user)
    return session.messages


@router.delete("/sessions/{session_id}/messages", response_model=MessageResponse)
def clear_chat(session_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    session = _get_session_or_404(db, session_id, user)
    for message in list(session.messages):
        db.delete(message)
    session.title = "New conversation"
    db.commit()
    return MessageResponse(message="Chat cleared")


@router.delete("/sessions/{session_id}", response_model=MessageResponse)
def delete_session(session_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    session = _get_session_or_404(db, session_id, user)
    db.delete(session)
    db.commit()
    return MessageResponse(message="Conversation deleted")


# --- Send message (streaming) ---
@router.post("/sessions/{session_id}/messages")
async def send_message(
    session_id: str,
    payload: chat_schema.ChatSendRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    session = _get_session_or_404(db, session_id, user)

    # Persist the user message immediately.
    db.add(ChatMessage(session_id=session.id, role="user", content=payload.message))
    session.updated_at = _now_naive()
    db.commit()

    history = [
        {"role": m.role, "content": m.content}
        for m in (db.query(ChatMessage).filter(ChatMessage.session_id == session.id).all())[-21:-1]
    ]
    analysis = ai_rules.build_analysis(payload.message)

    # If the backend rules allow it, persist an AI ticket draft now.
    draft = None
    if analysis["should_create_ticket"]:
        draft = ai_ticket.create_draft(db, user, session.id, analysis)

    async def event_stream() -> AsyncIterator[str]:
        reply_parts: list[str] = []
        try:
            async for chunk in ai_service.stream_reply(history, payload.message, analysis):
                reply_parts.append(chunk)
                yield _sse({"type": "token", "content": chunk})
            reply = "".join(reply_parts) or "I'm sorry, I couldn't generate a response."
            yield _sse({"type": "analysis", "analysis": analysis})
            if draft is not None:
                yield _sse({"type": "draft", "draft": {
                    "id": draft.id, "title": draft.title, "category": draft.category,
                    "priority": draft.priority, "department": draft.department,
                    "confidence": draft.confidence, "intent": draft.intent,
                }})
            yield _sse({"type": "done"})
        finally:
            # Persist the assistant reply. The request `db` session stays open
            # while the streaming response is generated (dependency teardown runs
            # after the body has been sent), so we commit through it to guarantee
            # the reply appears in the same database as the user message.
            if reply_parts:
                db.add(ChatMessage(
                    session_id=session.id,
                    role="assistant",
                    content="".join(reply_parts),
                    intent=analysis["intent"],
                ))
                session.updated_at = _now_naive()
                session.title = "".join(reply_parts).split("\n")[0][:80]
                db.commit()

    return StreamingResponse(event_stream(), media_type="text/event-stream")


# --- Drafts ---
@router.get("/drafts", response_model=list[chat_schema.AiTicketDraftRead])
def list_drafts(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    drafts = (
        db.query(AiTicketDraft)
        .filter(AiTicketDraft.user_id == user.id, AiTicketDraft.status == DraftStatus.PENDING.value)
        .order_by(AiTicketDraft.created_at.desc())
        .all()
    )
    return drafts


@router.post("/drafts/{draft_id}/confirm", response_model=chat_schema.AiTicketDraftRead)
def confirm_draft(draft_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    draft = ai_ticket.get_draft_or_404(db, draft_id, user)
    ticket = ai_ticket.confirm_draft(db, user, draft)
    create_notification(db, draft.user_id, "ticket_created",
                        "Ticket created from AI recommendation",
                        f"Your AI-proposed ticket {ticket.ticket_no} has been created.", ticket.id, commit=False)
    db.commit()
    return chat_schema.AiTicketDraftRead.model_validate(draft)


@router.post("/drafts/{draft_id}/dismiss", response_model=MessageResponse)
def dismiss_draft(draft_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    draft = ai_ticket.get_draft_or_404(db, draft_id, user)
    draft.status = DraftStatus.DISMISSED.value
    db.commit()
    return MessageResponse(message="Draft dismissed")