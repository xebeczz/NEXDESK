"""Email delivery service.

Sends via SMTP when configured; otherwise logs the message to the server
console so the reset flow remains testable in development.
"""
from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage

from app.core.config import settings

logger = logging.getLogger("itdesk.email")
logger.setLevel(logging.INFO)
if not logger.handlers:
    logger.addHandler(logging.StreamHandler())
    logger.propagate = False


def _send_smtp(to_email: str, subject: str, body: str) -> None:
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = settings.SMTP_FROM
    msg["To"] = to_email
    msg.set_content(body)
    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
        if settings.SMTP_USER:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.send_message(msg)


def send_email(to_email: str, subject: str, body: str) -> None:
    if settings.SMTP_HOST:
        try:
            _send_smtp(to_email, subject, body)
            logger.info("Email sent to %s", to_email)
        except Exception:  # pragma: no cover - SMTP failures must not break the API
            logger.exception("Failed to send email to %s", to_email)
        return
    # Development: print instead of sending (guaranteed visible to the console).
    import sys

    print(f"\n[DEV EMAIL] To: {to_email} | Subject: {subject}\n{body}\n", file=sys.stderr, flush=True)


def send_password_reset_email(to_email: str, reset_token: str) -> None:
    reset_url = f"{settings.FRONTEND_ORIGIN}/reset-password?token={reset_token}"
    body = (
        "You requested a password reset for your ITDesk account.\n\n"
        f"Click the link below to set a new password (valid for 30 minutes):\n\n"
        f"{reset_url}\n\n"
        "If you did not request this, you can safely ignore this email."
    )
    send_email(to_email, "ITDesk — Password Reset", body)