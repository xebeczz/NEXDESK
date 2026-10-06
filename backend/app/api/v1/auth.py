"""Authentication and account management endpoints."""
from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.deps import get_current_user
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.db.session import get_db
from app.db.base import ensure_aware
from app.models.enums import NotificationType, UserRole
from app.models.user import User
from app.schemas.auth import (
    ForgotPasswordRequest,
    LoginRequest,
    ResetPasswordRequest,
    TokenResponse,
)
from app.schemas.common import MessageResponse
from app.schemas.user import UserCreate, UserRead
from app.services.audit_service import log_action
from app.services.email_service import send_password_reset_email
from app.services.notification_service import create_notification

router = APIRouter(prefix="/auth", tags=["auth"])

REFRESH_COOKIE = "itdesk_refresh"
RESET_TOKEN_TTL = timedelta(minutes=30)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=REFRESH_COOKIE,
        value=token,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        httponly=True,
        samesite="lax",
        secure=not settings.DEBUG,
        path="/",
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(REFRESH_COOKIE, path="/")


def _to_token_response(user: User) -> TokenResponse:
    return TokenResponse(
        access_token=create_access_token(user.id),
        token_type="bearer",
        user=UserRead.model_validate(user),
    )


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Session = Depends(get_db)) -> TokenResponse:
    existing = (
        db.query(User)
        .filter(or_(User.email == payload.email, User.username == payload.username))
        .one_or_none()
    )
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email or username already in use")

    # Validate admin registration code if role is admin
    if payload.role == UserRole.ADMIN:
        if not payload.admin_registration_code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Admin registration code is required"
            )
        if payload.admin_registration_code != settings.ADMIN_REGISTRATION_CODE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid admin registration code"
            )

    try:
        user = User(
            email=payload.email,
            username=payload.username,
            full_name=payload.full_name,
            department=payload.department,
            hashed_password=hash_password(payload.password),
            role=payload.role,
        )
        db.add(user)
        db.flush()
        log_action(db, user.id, "user.register", "user", user.id, {"email": user.email, "role": user.role.value})
        db.commit()
        return _to_token_response(user)
    except Exception as err:
        db.rollback()
        if isinstance(err, HTTPException):
            raise err
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(err)}"
        )


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)) -> TokenResponse:
    user = (
        db.query(User)
        .filter(or_(User.email == payload.identifier, User.username == payload.identifier))
        .one_or_none()
    )
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This account is disabled")

    # If role is specified in request, validate it matches the user's role
    if payload.role is not None and user.role != payload.role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid role for this account")

    user.touch_login()
    log_action(db, user.id, "auth.login", "user", user.id)
    create_notification(
        db,
        user.id,
        NotificationType.LOGIN_SUCCESS.value,
        "Signed in",
        f"Welcome back, {user.full_name}.",
        commit=False,
    )
    db.commit()

    _set_refresh_cookie(response, create_refresh_token(user.id))
    return _to_token_response(user)


@router.post("/refresh", response_model=TokenResponse)
def refresh(request: Request, response: Response, db: Session = Depends(get_db)) -> TokenResponse:
    token = request.cookies.get(REFRESH_COOKIE)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing refresh token")
    try:
        payload = decode_token(token, expected_type="refresh")
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired or invalid")
    user = db.get(User, payload.get("sub"))
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Account inactive or removed")
    user.touch_login()
    db.commit()
    _set_refresh_cookie(response, create_refresh_token(user.id))
    return _to_token_response(user)


@router.post("/logout", response_model=MessageResponse)
def logout(response: Response) -> MessageResponse:
    _clear_refresh_cookie(response)
    return MessageResponse(message="Signed out")


@router.post("/forgot-password", response_model=MessageResponse)
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)) -> MessageResponse:
    message = MessageResponse(message="If that email exists, a reset link has been sent.")
    user = db.query(User).filter(User.email == payload.email).one_or_none()
    if user is None:
        return message
    token = secrets.token_urlsafe(32)
    user.password_reset_token = token
    user.password_reset_expires = _now() + RESET_TOKEN_TTL
    db.commit()
    send_password_reset_email(user.email, token)
    log_action(db, None, "password.reset_requested", "user", user.id)
    db.commit()
    return message


@router.post("/reset-password", response_model=MessageResponse)
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)) -> MessageResponse:
    user = db.query(User).filter(User.password_reset_token == payload.token).one_or_none()
    expires = ensure_aware(user.password_reset_expires) if user is not None else None
    if user is None or expires is None or expires < _now():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired reset token")
    user.hashed_password = hash_password(payload.new_password)
    user.password_reset_token = None
    user.password_reset_expires = None
    db.commit()
    log_action(db, user.id, "password.reset_completed", "user", user.id)
    db.commit()
    return MessageResponse(message="Password updated successfully. You can now sign in.")


@router.get("/me", response_model=UserRead)
def me(user: User = Depends(get_current_user)) -> User:
    return user