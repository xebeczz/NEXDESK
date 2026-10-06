"""Deterministic intent detection and ticket-decision rules.

This is the backend's validation layer for AI output. Regardless of which
provider (NVIDIA or offline fallback) generated suggestions, ticket creation is
gated here: greetings, small talk, general questions, and ordinary
troubleshooting never produce a ticket.
"""
from __future__ import annotations

import re

GREETING = "greeting"
CONVERSATION = "general_conversation"
PASSWORD_RESET = "password_reset"
EMAIL = "email"
VPN = "vpn"
PRINTER = "printer"
SOFTWARE = "software_installation"
HARDWARE = "hardware_failure"
NETWORK = "network"
SECURITY = "security"
BUG = "bug_report"
TICKET_CREATE = "ticket_creation"
TICKET_STATUS = "ticket_status"
KNOWLEDGE = "knowledge_request"
QUESTION = "general_question"

# --- Sentiment Analysis ---
SENTIMENT_POSITIVE = "positive"
SENTIMENT_NEUTRAL = "neutral"
SENTIMENT_NEGATIVE = "negative"
SENTIMENT_URGENT = "urgent/distressed"

# Urgency/distress indicators (words that signal urgency but NOT priority alone)
URGENCY_KEYWORDS = [
    "urgent", "urgently", "asap", "immediately", "emergency", "critical",
    "please help", "help me", "need help", "stuck", "cannot work",
    "blocked", "frustrated", "very frustrated", "extremely frustrated",
    "not working at all", "completely broken", "totally down",
]

# Negative sentiment indicators
NEGATIVE_KEYWORDS = [
    "not working", "broken", "failed", "error", "issue", "problem",
    "cannot", "can't", "unable", "won't", "doesn't", "isn't",
    "keeps crashing", "keeps failing", "repeatedly", "always",
    "never works", "constantly", "frequently",
]

# Positive sentiment indicators
POSITIVE_KEYWORDS = [
    "thank", "thanks", "appreciate", "great", "good", "working well",
    "solved", "fixed", "resolved", "helpful",
]

# --- Affected Users Detection ---
MULTI_USER_PATTERNS = [
    "all users", "everyone", "all employees", "all staff", "whole company",
    "company-wide", "company wide", "multiple users", "multiple people",
    "all departments", "every department", "across departments",
    "entire department", "whole department", "all of us",
    "nobody can", "no one can", "everyone is",
]

# Single user indicators
SINGLE_USER_PATTERNS = [
    "my ", "i ", "me ", "myself", "just me", "only me",
    "on my computer", "on my laptop", "on my pc",
]

# --- Workaround Detection ---
WORKAROUND_POSITIVE = [
    "restart", "reboot", "reconnect", "try again", "workaround",
    "temporary fix", "quick fix", "simple fix", "easy fix",
]

WORKAROUND_NEGATIVE = [
    "no workaround", "no fix", "cannot fix", "can't fix",
    "no solution", "nothing works", "tried everything",
    "already tried", "still not working", "didn't work",
]

INTENT_KEYWORDS: dict[str, list[str]] = {
    GREETING: ["hi", "hello", "hey", "good morning", "good afternoon", "good evening",
               "howdy", "ciao", "hola", "yo"],
    CONVERSATION: ["how are you", "what's up", "nice to meet", "thank you", "thanks",
                   "you're welcome", "bye", "goodbye", "have a good day"],
    PASSWORD_RESET: ["password", "reset password", "forgot password", "change password",
                     "login issue", "can't log in", "cannot log in", "locked out",
                     "sign in", "credentials"],
    EMAIL: ["email", "mailbox", "outlook", "gmail", "send email", "receive email",
            "email sync", "spam", "inbox", "not receiving emails", "emails not coming"],
    VPN: ["vpn", "virtual private network", "vpn client", "remote access", "connect to vpn",
          "vpn not connecting", "vpn won't connect", "vpn failing"],
    PRINTER: ["printer", "print", "printing", "paper jam", "toner", "scanner", "scan",
              "printer not printing", "not printing", "won't print"],
    SOFTWARE: ["install", "install software", "application", "software", "upgrade",
               "update software", "download software", "license", "uninstall"],
    NETWORK: ["internet", "wifi", "wi-fi", "wireless", "network", "connection",
              "slow internet", "no internet", "can't connect", "cannot connect", "ethernet",
              "wifi not working", "wifi is not working", "my wifi", "wi-fi not working",
              "wireless not working", "no wifi", "wifi down", "wifi issues"],
    HARDWARE: ["computer", "screen", "monitor", "keyboard", "blue screen",
               "overheat", "overheating", "fan", "battery", "crash", "shut down",
               "won't boot", "wont boot", "hardware", "hard drive", "laptop hardware",
               "laptop screen", "laptop keyboard", "laptop battery"],
    SECURITY: ["security", "breach", "security incident", "malware", "virus",
               "phishing", "ransomware", "hacked", "hacker", "unauthorized"],
    BUG: ["bug", "glitch", "error", "not working", "broken", "crash", "freeze",
          "freezing", "fails", "failure", "report a bug"],
    TICKET_CREATE: ["create a ticket", "open a ticket", "raise a ticket", "file a ticket",
                    "log a ticket", "submit a ticket", "make a ticket", "need a ticket"],
    TICKET_STATUS: ["ticket status", "status of my ticket", "where is my ticket",
                    "check my ticket", "my ticket", "track my ticket"],
    KNOWLEDGE: ["how do i", "how can i", "how to", "instructions", "guide",
                "walk me through", "steps", "tell me how"],
    QUESTION: ["what is", "who", "when", "where", "why", "which"],
}

CRITICAL_PATTERNS = [
    "server down", "server is down", "server is completely down", "server completely down",
    "production down", "production server down", "prod down",
    "database down", "database failure", "db down", "database crash",
    "security breach", "data breach", "breach",
    "outage", "network outage", "internet down", "company-wide", "company wide",
    "multiple users", "multiple departments", "all users", "everyone", "whole company",
    "all departments", "every department", "across departments",
    "ransomware", "virus outbreak", "attack",
    "email down", "email outage", "systems down", "business stopped",
    "completely down", "totally down",
]
TROUBLESHOOT_FAILED = [
    "didn't work", "did not work", "still not working", "still broken",
    "no luck", "not fixed", "still happening", "tried that", "already tried",
    "that didn't help", "doesn't work", "still fails",
]

CATEGORY_BY_INTENT = {
    EMAIL: "Email", VPN: "Network & VPN", PRINTER: "Hardware & Equipment",
    SOFTWARE: "Software", HARDWARE: "Hardware", NETWORK: "Network & VPN",
    SECURITY: "Security", PASSWORD_RESET: "Identity & Access",
}

DEPT_BY_CATEGORY = {
    "Email": "IT Support",
    "Network & VPN": "IT Operations",
    "Hardware & Equipment": "IT Support",
    "Hardware": "IT Support",
    "Software": "Software Services",
    "Security": "Security",
    "Identity & Access": "IT Support",
    "IT Operations": "IT Operations",
    "General": "IT Support",
}


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def _KW(keyword: str) -> re.Pattern:
    return re.compile(r"\b" + re.escape(keyword) + r"\b")


# --- Sentiment Analysis Functions ---

def detect_sentiment(text: str) -> str:
    """Detect the user's sentiment from their message.

    Returns one of: positive, neutral, negative, urgent/distressed
    """
    t = _norm(text)

    # Check for urgency/distress first
    urgency_score = sum(1 for kw in URGENCY_KEYWORDS if kw in t)
    negative_score = sum(1 for kw in NEGATIVE_KEYWORDS if kw in t)
    positive_score = sum(1 for kw in POSITIVE_KEYWORDS if kw in t)

    # Urgency/distress if multiple urgency indicators or strong distress
    if urgency_score >= 2 or (urgency_score >= 1 and negative_score >= 3):
        return SENTIMENT_URGENT

    # Positive sentiment
    if positive_score > negative_score and positive_score >= 1:
        return SENTIMENT_POSITIVE

    # Negative sentiment
    if negative_score > positive_score and negative_score >= 2:
        return SENTIMENT_NEGATIVE

    # Default to neutral
    return SENTIMENT_NEUTRAL


def detect_affected_users(text: str) -> str:
    """Detect how many users are affected.

    Returns: 'single', 'multiple', or 'organization'
    """
    t = _norm(text)

    # Check for organization-wide patterns
    org_patterns = ["company-wide", "company wide", "whole company", "all users",
                    "all employees", "all staff", "nobody can", "no one can"]
    if any(p in t for p in org_patterns):
        return "organization"

    # Check for department/multiple user patterns
    multi_patterns = ["all users", "everyone", "multiple users", "multiple people",
                      "all departments", "entire department", "whole department", "all of us"]
    if any(p in t for p in multi_patterns):
        return "multiple"

    # Check for single user indicators
    single_patterns = ["my ", "i ", "me ", "myself", "just me", "only me",
                       "on my computer", "on my laptop", "on my pc"]
    if any(p in t for p in single_patterns):
        return "single"

    # Default to single if unclear
    return "single"


def detect_workaround_available(text: str) -> bool:
    """Check if the user mentions or implies a workaround exists."""
    t = _norm(text)

    # Positive workaround indicators
    if any(p in t for p in WORKAROUND_POSITIVE):
        return True

    # Negative workaround indicators
    if any(p in t for p in WORKAROUND_NEGATIVE):
        return False

    return False


def detect_production_impact(text: str) -> bool:
    """Check if production systems are affected."""
    t = _norm(text)

    production_patterns = [
        "production", "prod server", "prod system", "live system",
        "customer facing", "customer-facing", "revenue", "business critical",
        "database down", "db down", "server down",
    ]
    return any(p in t for p in production_patterns)


def detect_intent(text: str) -> tuple[str, float]:
    """Return (intent, confidence) based on whole-word keyword scoring."""
    t = _norm(text)
    best, best_score = QUESTION, 0
    for intent, keywords in INTENT_KEYWORDS.items():
        score = sum(1 for kw in keywords if _KW(kw).search(t))
        if score > best_score:
            best, best_score = intent, score
    if best_score == 0:
        return QUESTION, 0.4
    return best, min(0.95, 0.4 + 0.2 * best_score)


def is_clear_greeting(text: str) -> bool:
    intent, _ = detect_intent(text)
    return intent in (GREETING, CONVERSATION)


def is_critical(text: str) -> bool:
    t = _norm(text)
    return any(p in t for p in CRITICAL_PATTERNS)


def wants_ticket(text: str) -> bool:
    t = _norm(text)
    return any(kw in t for kw in INTENT_KEYWORDS[TICKET_CREATE])


def troubleshooting_failed(text: str) -> bool:
    t = _norm(text)
    return not _is_clear(t) and any(p in t for p in TROUBLESHOOT_FAILED)


def _is_clear(text: str) -> bool:
    intent, _ = detect_intent(text)
    return intent in (GREETING, CONVERSATION)


def _category_for(text: str, intent: str) -> str:
    if is_critical(text):
        return "IT Operations"
    return CATEGORY_BY_INTENT.get(intent, "General")


def build_analysis(user_text: str) -> dict:
    """Deterministic structured analysis used to gate any ticket creation.

    Uses sentiment analysis, impact assessment, and severity detection
    to determine priority.
    """
    intent, confidence = detect_intent(user_text)
    critical = is_critical(user_text)
    explicit = wants_ticket(user_text)
    failed = troubleshooting_failed(user_text)
    clear = _is_clear(user_text)

    # New: Sentiment and impact analysis
    sentiment = detect_sentiment(user_text)
    affected_users = detect_affected_users(user_text)
    workaround = detect_workaround_available(user_text)
    production = detect_production_impact(user_text)

    category: str = _category_for(user_text, intent)
    priority: str
    department: str | None

    # --- NEW PRIORITY METHODOLOGY ---
    # Consider: sentiment, urgency, technical severity, affected users,
    # business impact, workaround availability, and nature of issue

    # CRITICAL: Production systems down, organization-wide outage, severe security
    if critical or production:
        priority = "critical"
        department = DEPT_BY_CATEGORY.get("IT Operations")
    # Also critical if many users affected + no workaround + production-like severity
    elif affected_users == "organization" and not workaround:
        priority = "critical"
        department = DEPT_BY_CATEGORY.get("IT Operations")
    # HIGH: Multiple users affected, important functionality unavailable, no workaround
    elif affected_users == "multiple" and not workaround:
        priority = "high"
        department = DEPT_BY_CATEGORY.get(category)
    # HIGH: Security issues
    elif intent in (SECURITY,):
        priority = "high"
        department = DEPT_BY_CATEGORY.get(category)
    # HIGH: Network outages affecting work (not VPN which is often single-user)
    elif intent == NETWORK and not workaround:
        priority = "high"
        department = DEPT_BY_CATEGORY.get(category)
    # MEDIUM: User's work is affected, persistent problem, limited workaround
    elif intent == VPN:
        # VPN: single user with work impact = Medium, otherwise Low
        t = _norm(user_text)
        work_impact = any(kw in t for kw in ["cannot work", "can't work", "unable to work",
                                              "cannot complete", "can't complete",
                                              "cannot complete my work", "can't complete my work",
                                              "cannot access", "can't access",
                                              "blocking", "blocked", "stop",
                                              "keeps disconnecting", "repeatedly",
                                              "failing all day", "all day"])
        if work_impact:
            priority = "medium"
        elif affected_users == "multiple":
            priority = "medium"
        else:
            priority = "low"
        department = DEPT_BY_CATEGORY.get(category)
    elif intent in (EMAIL, PASSWORD_RESET, BUG):
        if workaround and affected_users == "single":
            priority = "low"
        else:
            priority = "medium"
        department = DEPT_BY_CATEGORY.get(category)
    elif intent in (SOFTWARE, PRINTER, TICKET_STATUS):
        priority = "medium"
        department = DEPT_BY_CATEGORY.get(category)
    # HARDWARE: Consider the specific issue - minor hardware (keyboard, mouse) = low
    elif intent == HARDWARE:
        # Check for minor hardware issues
        minor_hardware = ["keyboard", "mouse", "monitor", "webcam", "microphone"]
        t = _norm(user_text)
        if any(hw in t for hw in minor_hardware) and affected_users == "single":
            priority = "low"
        else:
            priority = "medium"
        department = DEPT_BY_CATEGORY.get(category)
    # LOW: Minor issue, single user, easy workaround exists
    elif workaround and affected_users == "single":
        priority = "low"
        department = DEPT_BY_CATEGORY.get(category)
    else:
        priority, department = "medium", DEPT_BY_CATEGORY.get(category)

    # Context override: if user is clearly in distress but issue is minor,
    # still keep it at the appropriate technical priority
    # (sentiment is informational, not determinative)

    should_create = (explicit or critical or failed) and not clear

    return {
        "intent": intent,
        "confidence": round(confidence, 2),
        "priority": priority,
        "category": category,
        "department": department,
        "summary": _summarize(user_text, category),
        "should_create_ticket": True if should_create else False,
        "sentiment": sentiment,
    }


def _summarize(text: str, category: str) -> str:
    words = _norm(text).split()
    snippet = " ".join(words[:18]) or text
    return f"{category} issue reported: {snippet}"