"""AI helpdesk tests: deterministic rules + chat → draft → ticket flow."""
from __future__ import annotations

import json

from app.services import ai_rules
from app.services.ai_rules import detect_intent

from tests.conftest import make_user


def _parse_sse(body: str) -> list[dict]:
    events = []
    for frame in body.split("\n\n"):
        line = frame.strip()
        if line.startswith("data:"):
            events.append(json.loads(line[5:].strip()))
    return events


# --- Intent detection (whole-word matching) ---
def test_intent_greeting():
    intent, _ = detect_intent("Hello there!")
    assert intent in (ai_rules.GREETING, ai_rules.CONVERSATION)


def test_intent_not_substring_match():
    # "you" must not match the "yo" greeting keyword.
    intent, _ = detect_intent("Can you help me with my laptop?")
    assert intent != ai_rules.GREETING


def test_intent_email():
    intent, _ = detect_intent("My outlook email is not syncing")
    assert intent == ai_rules.EMAIL


def test_intent_password_reset():
    intent, _ = detect_intent("I forgot my password and cannot log in")
    assert intent == ai_rules.PASSWORD_RESET


# --- Ticket-decision rules ---
def test_greeting_never_creates_ticket():
    a = ai_rules.build_analysis("Hello, thanks for your help!")
    assert a["should_create_ticket"] is False


def test_critical_incident_creates_ticket():
    a = ai_rules.build_analysis("The production is down and multiple users are affected")
    assert a["should_create_ticket"] is True
    assert a["priority"] == "critical"


def test_explicit_request_creates_ticket():
    a = ai_rules.build_analysis("Please create a ticket, my monitor is broken")
    assert a["should_create_ticket"] is True


def test_troubleshooting_failed_creates_ticket():
    a = ai_rules.build_analysis("I tried restarting the printer but it still doesn't work")
    assert a["should_create_ticket"] is True


def test_general_question_does_not_create_ticket():
    a = ai_rules.build_analysis("What is the IT support number?")
    assert a["should_create_ticket"] is False


# --- Chat flow via API ---
def test_greeting_chat_no_draft(client, db, auth_headers):
    user = make_user(db)
    headers = auth_headers(user)
    session = client.post("/api/v1/chat/sessions", json={}, headers=headers).json()

    body = client.post(
        f"/api/v1/chat/sessions/{session['id']}/messages",
        json={"message": "Hello there!"},
        headers=headers,
    )
    assert body.status_code == 200, body.text
    events = _parse_sse(body.text)
    assert any(e["type"] == "analysis" for e in events)
    assert not any(e["type"] == "draft" for e in events)

    drafts = client.get("/api/v1/chat/drafts", headers=headers).json()
    assert drafts == []


def test_critical_chat_creates_draft_then_ticket(client, db, auth_headers):
    user = make_user(db)
    headers = auth_headers(user)
    session = client.post("/api/v1/chat/sessions", json={}, headers=headers).json()

    body = client.post(
        f"/api/v1/chat/sessions/{session['id']}/messages",
        json={"message": "The server is down, multiple users cannot work, security breach"},
        headers=headers,
    )
    assert body.status_code == 200, body.text
    events = _parse_sse(body.text)
    assert any(e["type"] == "draft" for e in events)

    drafts = client.get("/api/v1/chat/drafts", headers=headers).json()
    assert len(drafts) == 1
    assert drafts[0]["priority"] == "critical"

    confirmed = client.post(f"/api/v1/chat/drafts/{drafts[0]['id']}/confirm", headers=headers)
    assert confirmed.status_code == 200, confirmed.text

    # The draft is consumed; the ticket now exists.
    tickets = client.get("/api/v1/tickets", headers=headers).json()
    assert any(t["title"].startswith("[AI]") for t in tickets["items"])


def test_chat_session_persists_history(client, db, auth_headers):
    user = make_user(db)
    headers = auth_headers(user)
    session = client.post("/api/v1/chat/sessions", json={}, headers=headers).json()

    client.post(
        f"/api/v1/chat/sessions/{session['id']}/messages",
        json={"message": "My printer is jammed"},
        headers=headers,
    )
    msgs = client.get(f"/api/v1/chat/sessions/{session['id']}/messages", headers=headers).json()
    assert len(msgs) >= 2
    assert msgs[0]["role"] == "user"
    assert msgs[-1]["role"] == "assistant"