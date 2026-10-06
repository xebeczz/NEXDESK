"""Settings endpoints for user preferences."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.security import hash_password, verify_password
from app.db.session import get_db
from app.models.user import User
from app.schemas.settings import (
    NotificationPreferences,
    PasswordChange,
    ProfileUpdate,
    SecuritySettings,
    SettingsResponse,
    ThemePreference,
)
from app.schemas.user import UserRead
from app.services.audit_service import log_action

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("", response_model=SettingsResponse)
def get_settings(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> SettingsResponse:
    """Get all user settings."""
    theme_pref = ThemePreference(theme=user.theme_preference)
    notif_prefs = user.get_notification_preferences()
    security_settings = SecuritySettings(
        two_factor_enabled=user.two_factor_enabled,
        last_password_change=user.last_password_change.isoformat() if user.last_password_change else None,
    )
    return SettingsResponse(
        user=UserRead.model_validate(user),
        theme_preference=theme_pref,
        notification_preferences=NotificationPreferences(**notif_prefs),
        security_settings=security_settings,
    )


@router.patch("/profile", response_model=UserRead)
def update_profile(
    payload: ProfileUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> User:
    """Update user profile information."""
    # Check if email is being changed and if it's already taken
    if payload.email != user.email:
        existing = db.query(User).filter(User.email == payload.email, User.id != user.id).one_or_none()
        if existing is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already in use")

    # Check if username is being changed and if it's already taken
    if payload.username != user.username:
        existing = db.query(User).filter(User.username == payload.username, User.id != user.id).one_or_none()
        if existing is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already taken")

    changes = {}
    if payload.full_name != user.full_name:
        user.full_name = payload.full_name
        changes["full_name"] = payload.full_name
    if payload.department != user.department:
        user.department = payload.department
        changes["department"] = payload.department
    if payload.username != user.username:
        user.username = payload.username
        changes["username"] = payload.username
    if payload.email != user.email:
        user.email = payload.email
        changes["email"] = payload.email

    if changes:
        db.commit()
        db.refresh(user)
        log_action(db, user.id, "settings.profile_updated", "user", user.id, changes)
        db.commit()

    return user


@router.patch("/password", status_code=status.HTTP_200_OK)
def change_password(
    payload: PasswordChange,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Change user password."""
    if not verify_password(payload.current_password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect")

    user.hashed_password = hash_password(payload.new_password)
    user.last_password_change = datetime.utcnow()
    db.commit()
    log_action(db, user.id, "settings.password_changed", "user", user.id)
    db.commit()

    return {"message": "Password updated successfully"}


@router.patch("/appearance", response_model=ThemePreference)
def update_appearance(
    payload: ThemePreference,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ThemePreference:
    """Update appearance/theme preference."""
    user.theme_preference = payload.theme
    db.commit()
    db.refresh(user)
    log_action(db, user.id, "settings.appearance_updated", "user", user.id, {"theme": payload.theme})
    db.commit()

    return payload


@router.patch("/notifications", response_model=NotificationPreferences)
def update_notifications(
    payload: NotificationPreferences,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> NotificationPreferences:
    """Update notification preferences."""
    user.set_notification_preferences(payload.model_dump())
    db.commit()
    db.refresh(user)
    log_action(db, user.id, "settings.notifications_updated", "user", user.id, payload.model_dump())
    db.commit()

    return payload


@router.get("/security", response_model=SecuritySettings)
def get_security_settings(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> SecuritySettings:
    """Get security settings."""
    return SecuritySettings(
        two_factor_enabled=user.two_factor_enabled,
        last_password_change=user.last_password_change.isoformat() if user.last_password_change else None,
    )


@router.post("/security/2fa/enable", response_model=dict)
def enable_2fa(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Enable two-factor authentication (generates secret and QR code)."""
    import pyotp
    import qrcode
    import io
    import base64

    if user.two_factor_enabled:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="2FA is already enabled")

    # Generate secret
    secret = pyotp.random_base32()
    user.two_factor_secret = secret
    db.commit()

    # Generate QR code
    totp = pyotp.TOTP(secret)
    provisioning_uri = totp.provisioning_uri(name=user.email, issuer_name="ITDesk")

    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(provisioning_uri)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()

    return {
        "secret": secret,
        "qr_code": f"data:image/png;base64,{qr_code_base64}",
        "uri": provisioning_uri,
    }


@router.post("/security/2fa/verify", response_model=dict)
def verify_2fa(
    code: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Verify 2FA code and enable 2FA if valid."""
    import pyotp

    if not user.two_factor_secret:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="2FA not set up")

    totp = pyotp.TOTP(user.two_factor_secret)
    if not totp.verify(code, valid_window=1):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid 2FA code")

    user.two_factor_enabled = True
    db.commit()
    log_action(db, user.id, "settings.2fa_enabled", "user", user.id)
    db.commit()

    return {"message": "Two-factor authentication enabled successfully"}


@router.post("/security/2fa/disable", response_model=dict)
def disable_2fa(
    code: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Disable two-factor authentication."""
    import pyotp

    if not user.two_factor_enabled:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="2FA is not enabled")

    totp = pyotp.TOTP(user.two_factor_secret)
    if not totp.verify(code, valid_window=1):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid 2FA code")

    user.two_factor_enabled = False
    user.two_factor_secret = None
    db.commit()
    log_action(db, user.id, "settings.2fa_disabled", "user", user.id)
    db.commit()

    return {"message": "Two-factor authentication disabled successfully"}


# Import at bottom to avoid circular imports
from datetime import datetime