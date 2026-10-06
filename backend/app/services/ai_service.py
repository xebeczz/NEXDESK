"""AI helpdesk service.

Uses NVIDIA's OpenAI-compatible Chat Completions API when ``NVIDIA_API_KEY`` is
set; otherwise an offline, deterministic provider keeps every AI feature fully
functional for local development and testing.
"""
from __future__ import annotations

import json
import logging
from typing import AsyncIterator

import httpx

from app.core.config import settings
from app.services import ai_rules

logger = logging.getLogger("itdesk.ai")
if not logger.handlers:
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.INFO)
    logger.propagate = False

SYSTEM_PROMPT = """You are a professional IT Helpdesk assistant for an enterprise company.

Your behavior:
- Hold natural, friendly conversations. Greet warmly, ask how you can help.
- Troubleshoot IT issues step by step: ask 1–2 clear follow-up questions when details are missing, then give concise, actionable steps.
- Explain solutions clearly in plain language. Keep replies short (under 120 words) unless asked for detail.
- NEVER create a ticket yourself.
- Only suggest that a ticket should be opened when the user explicitly asks for one, troubleshooting has failed, or the issue is critical (production server down, database failure, security breach, network outage, multiple users affected, hardware failure).
- When a ticket seems warranted, briefly recommend a category, priority (low/medium/high/critical), and department.

The user works at the company and may paste error messages or describe incidents. Be professional, empathetic, and precise."""


def _history_to_messages(history: list[dict]) -> list[dict]:
    """History is a list of {role, content} for user/assistant turns."""
    return [{"role": m["role"], "content": m["content"]} for m in history if m["role"] in ("user", "assistant")]


def fallback_reply(intent: str, user_text: str, analysis: dict) -> str:
    """Offline, scripted helpdesk reply based on the detected intent."""
    t = user_text.strip()
    if intent == ai_rules.GREETING:
        return "Hello! Welcome to the IT Helpdesk. 👋 How can I assist you today?"
    if intent == ai_rules.CONVERSATION:
        if "thank" in t.lower() or "thanks" in t.lower():
            return "You're welcome! 😊 Is there anything else I can help you with?"
        if "how are you" in t.lower() or "how's" in t.lower():
            return "I'm doing well, thank you for asking! How can I help you today?"
        return "Happy to chat! How can I help you today?"
    if intent == ai_rules.TICKET_STATUS:
        return ("You can check your ticket status any time from the 'My Tickets' page in the dashboard. "
                "If you tell me your ticket number, I can guide you through what the statuses mean.")
    if intent == ai_rules.PASSWORD_RESET:
        return ("I can help with that. Password reset steps:\n1. On the login page, click 'Forgot password'.\n"
                "2. Enter your work email and follow the reset link you receive.\n"
                "3. Set a new password (min 8 characters).\n\n"
                "Is the reset email not arriving, or is something else going wrong?")
    if intent == ai_rules.NETWORK:
        return ("Let's troubleshoot your connectivity:\n1. Check that Wi-Fi is on and the correct network is selected.\n"
                "2. Try toggling Airplane mode on/off, or restart the router.\n"
                "3. Run `ipconfig /release` then `ipconfig /renew` on Windows.\n\n"
                "Does the network come back, or is it still down?")
    if intent == ai_rules.PRINTER:
        return ("Let's sort out the printer:\n1. Confirm the printer shows online (check the panel lights).\n"
                "2. Restart the print spooler: Services > Print Spooler > Restart.\n"
                "3. Re-add the printer from Windows Settings > Devices.\n\n"
                "Try printing a test page and let me know if it goes through.")
    if intent == ai_rules.EMAIL:
        return ("Let's fix your email:\n1. Verify the server shows Connected in Outlook's status bar.\n"
                "2. Run Outlook in Safe mode (hold Ctrl while opening) to rule out add-ins.\n"
                "3. Check your inbox size and clear the Deleted Items if near quota.\n\n"
                "Are messages queued, or is Outlook showing a specific error?")
    if intent == ai_rules.SOFTWARE:
        return ("I can help with software installation. Which application do you need, and do you have "
                "an administrator to approve the license? I can outline the request and create a ticket "
                "for the Software team if you'd like.")
    if intent == ai_rules.HARDWARE:
        return ("A hardware issue can be disruptive. Let's gather a few details:\n1. Does the device power on? "
                "2. Any error lights or beeps?\n3. Is it a laptop or desktop?\n\n"
                "If it's not powering on at all, we may need to open a ticket for the hardware team — "
                "want me to create that for you?")
    if intent == ai_rules.SECURITY:
        return ("Security concerns are handled urgently. Please do not click any suspicious links or share "
                "credentials. Could you describe what you're seeing (email, popup, or account alert)? "
                "We should open a security ticket right away.")
    if analysis.get("should_create_ticket"):
        return ("I can open a ticket for you with the details you've shared. "
                "Would you like me to create it?")
    return ("Thanks for the details. I'd like to ask one or two follow-up questions so I can give you the "
            "most accurate fix — could you tell me a bit more about what's happening?")


class AiService:
    """Streams an assistant reply, always grounded by backend rule validation."""

    @property
    def enabled(self) -> bool:
        return settings.is_ai_enabled

    async def stream_reply(self, history: list[dict], user_text: str, analysis: dict) -> AsyncIterator[str]:
        if self.enabled:
            async for chunk in self._stream_nvidia(history, user_text, analysis):
                yield chunk
        else:
            reply = fallback_reply(analysis["intent"], user_text, analysis)
            # Yield in a few chunks so the UI still shows a typing/stream effect.
            for chunk in _chunk_text(reply):
                yield chunk

    async def _stream_nvidia(self, history: list[dict], user_text: str, analysis: dict) -> AsyncIterator[str]:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages.extend(_history_to_messages(history))
        messages.append({"role": "user", "content": user_text})
        url = f"{settings.NVIDIA_BASE_URL.rstrip('/')}/chat/completions"
        headers = {"Authorization": f"Bearer {settings.NVIDIA_API_KEY}"}
        payload = {
            "model": settings.NVIDIA_MODEL,
            "messages": messages,
            "stream": True,
            "temperature": 1,
            "top_p": 0.95,
            "max_tokens": 16384,
            "extra_body": {
                "chat_template_kwargs": {
                    "enable_thinking": True,
                },
                "reasoning_budget": 16384,
            },
        }
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                async with client.stream("POST", url, json=payload, headers=headers) as resp:
                    resp.raise_for_status()
                    async for line in resp.aiter_lines():
                        if not line.startswith("data:"):
                            continue
                        data = line[5:].strip()
                        if data == "[DONE]":
                            break
                        try:
                            obj = json.loads(data)
                        except json.JSONDecodeError:
                            continue
                        delta = (obj.get("choices") or [{}])[0].get("delta") or {}
                        # Consume reasoning_content but do NOT send it to the frontend.
                        # Only yield user-facing content.
                        content = delta.get("content")
                        if content:
                            yield content
        except Exception as exc:  # NOQA: BLE001 - degrade gracefully to offline
            logger.warning("NVIDIA streaming failed (%s); falling back to offline reply.", exc)
            fallback = fallback_reply(analysis.get("intent", ai_rules.QUESTION), user_text,
                                      {"should_create_ticket": False})
            for chunk in _chunk_text(fallback):
                yield chunk


def _chunk_text(text: str) -> list[str]:
    """Yield word-level tokens preserving spacing so concatenated chunks match original text exactly."""
    words = text.split(" ")
    chunks = []
    for i, word in enumerate(words):
        if i < len(words) - 1:
            chunks.append(word + " ")
        else:
            chunks.append(word)
    return chunks or [text]


ai_service = AiService()