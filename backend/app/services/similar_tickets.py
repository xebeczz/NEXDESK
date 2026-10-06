"""Similarity service for finding related tickets without external ML dependencies."""
from __future__ import annotations

import re

_SYNONYMS = {
    "vpn": ["vpn", "virtual", "private", "network", "connect", "disconnect", "connection"],
    "server": ["server", "service", "application", "app", "host", "system", "down", "unavailable", "responding"],
    "network": ["network", "lan", "wan", "internet", "wifi", "wireless", "ethernet", "cable", "connection", "connectivity"],
    "email": ["email", "mail", "outlook", "smtp", "inbox", "mailbox", "message"],
    "hardware": ["hardware", "laptop", "desktop", "computer", "keyboard", "monitor", "screen", "battery", "power", "printer"],
    "software": ["software", "application", "app", "install", "update", "browser", "pdf", "program"],
    "account": ["account", "login", "password", "access", "locked", "expired", "authentication", "mfa", "2fa", "user"],
    "security": ["security", "alert", "antivirus", "malware", "suspicious", "blocked", "quarantine"],
    "printer": ["printer", "print", "offline", "blank", "pages", "cartridge"],
    "database": ["database", "db", "sql", "connection", "query", "replication"],
    "backup": ["backup", "restore", "archive", "storage"],
    "dns": ["dns", "domain", "resolution", "resolve", "website"],
    "wifi": ["wifi", "wireless", "wi-fi", "authentication", "ssid"],
    "slow": ["slow", "performance", "lag", "cpu", "usage", "unresponsive", "freeze", "frozen"],
    "hot": ["hot", "overheat", "temperature", "fan", "cooling", "thermal"],
    "screen": ["screen", "display", "monitor", "flicker", "black", "hdmi"],
}

_STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "up", "about", "into", "through", "during",
    "before", "after", "above", "below", "between", "under", "again",
    "further", "then", "once", "here", "there", "when", "where", "why",
    "how", "all", "any", "both", "each", "few", "more", "most", "other",
    "some", "such", "no", "nor", "not", "only", "own", "same", "so",
    "than", "too", "very", "can", "will", "just", "don", "should", "now",
    "is", "am", "are", "was", "were", "be", "been", "being", "have",
    "has", "had", "having", "do", "does", "did", "doing", "would", "could",
    "ought", "i", "me", "my", "we", "our", "you", "your", "he", "him",
    "his", "she", "her", "it", "its", "they", "them", "their", "what",
    "which", "who", "whom", "this", "that", "these", "those", "im",
    "ive", "youre", "hes", "shes", "its", "were", "weve", "theyve",
    "id", "wed", "theyd", "ill", "youll", "hell", "shell", "theyll",
    "isnt", "arent", "wasnt", "werent", "hasnt", "havent", "hadnt",
    "doesnt", "dont", "didnt", "wont", "wouldnt", "cant", "couldnt",
    "mustnt", "lets", "thats", "whos", "whats", "heres", "theres",
    "whens", "wheres", "whys", "hows", "im", "cannot", "unable",
    "able", "get", "got", "getting", "please", "help", "need",
    "working", "work", "works", "worked", "working",
}


def _tokenize(text: str) -> set[str]:
    text = text.lower()
    words = re.findall(r"[a-z0-9]+", text)
    return {w for w in words if w not in _STOPWORDS and len(w) > 1}


def _expand_tokens(tokens: set[str]) -> set[str]:
    expanded = set(tokens)
    for token in tokens:
        for key, synonyms in _SYNONYMS.items():
            if token == key or token in synonyms:
                expanded.update(synonyms)
                expanded.add(key)
    return expanded


def _category_similarity(a: str | None, b: str | None) -> float:
    if not a or not b:
        return 0.0
    a_tokens = _tokenize(a)
    b_tokens = _tokenize(b)
    if not a_tokens or not b_tokens:
        return 0.0
    inter = a_tokens & b_tokens
    union = a_tokens | b_tokens
    return len(inter) / len(union) if union else 0.0


def compute_similarity(
    current_title: str,
    current_description: str,
    current_category: str | None,
    current_priority: str | None,
    current_department: str | None,
    candidate_title: str,
    candidate_description: str,
    candidate_category: str | None,
    candidate_priority: str | None,
    candidate_department: str | None,
    candidate_status: str | None,
) -> float:
    """Return a similarity score from 0.0 to 100.0."""
    title_tokens = _expand_tokens(_tokenize(current_title))
    desc_tokens = _expand_tokens(_tokenize(current_description))
    query_tokens = title_tokens | desc_tokens

    cand_title_tokens = _expand_tokens(_tokenize(candidate_title))
    cand_desc_tokens = _expand_tokens(_tokenize(candidate_description))
    cand_tokens = cand_title_tokens | cand_desc_tokens

    if not query_tokens or not cand_tokens:
        return 0.0

    title_jaccard = len(title_tokens & cand_title_tokens) / len(title_tokens | cand_title_tokens) if (title_tokens | cand_title_tokens) else 0.0
    desc_jaccard = len(desc_tokens & cand_desc_tokens) / len(desc_tokens | cand_desc_tokens) if (desc_tokens | cand_desc_tokens) else 0.0
    full_jaccard = len(query_tokens & cand_tokens) / len(query_tokens | cand_tokens) if (query_tokens | cand_tokens) else 0.0

    cat_sim = _category_similarity(current_category, candidate_category)

    dept_sim = 0.0
    if current_department and candidate_department:
        dept_sim = _category_similarity(current_department, candidate_department)

    priority_boost = 0.0
    if current_priority and candidate_priority and current_priority == candidate_priority:
        priority_boost = 0.08

    status_boost = 0.0
    if candidate_status in ("resolved", "closed"):
        status_boost = 0.08

    # Base score from category similarity
    base_score = 0.0
    if current_category and candidate_category:
        if current_category.lower().strip() == candidate_category.lower().strip():
            base_score = 0.70
        else:
            base_score = cat_sim * 0.35

    # Title overlap boost
    title_overlap = title_jaccard * 0.20

    # Description overlap boost
    desc_overlap = desc_jaccard * 0.10

    # Full text overlap boost
    full_overlap = full_jaccard * 0.10

    priority_boost = 0.0
    if current_priority and candidate_priority and current_priority == candidate_priority:
        priority_boost = 0.05

    status_boost = 0.0
    if candidate_status in ("resolved", "closed"):
        status_boost = 0.05

    score = (
        base_score
        + title_overlap
        + desc_overlap
        + full_overlap
        + priority_boost
        + status_boost
    )

    return round(min(100.0, max(0.0, score * 100)), 1)


def find_similar_tickets(
    db,
    current_title: str,
    current_description: str,
    current_category: str | None = None,
    current_priority: str | None = None,
    current_department: str | None = None,
    *,
    threshold: float = 70.0,
    limit: int = 5,
    exclude_ticket_id: str | None = None,
) -> list[dict]:
    """Search the database for tickets similar to the current issue."""
    from app.models.ticket import Ticket
    from app.services.ticket_service import build_detail

    q = db.query(Ticket)
    if exclude_ticket_id:
        q = q.filter(Ticket.id != exclude_ticket_id)

    candidates = q.all()

    scored: list[dict] = []
    for ticket in candidates:
        sim = compute_similarity(
            current_title=current_title,
            current_description=current_description,
            current_category=current_category,
            current_priority=current_priority,
            current_department=current_department,
            candidate_title=ticket.title,
            candidate_description=ticket.description,
            candidate_category=ticket.category,
            candidate_priority=ticket.priority.value if hasattr(ticket.priority, "value") else str(ticket.priority),
            candidate_department=ticket.department,
            candidate_status=ticket.status,
        )
        if sim >= threshold:
            detail = build_detail(ticket)
            scored.append({
                "ticket_id": ticket.id,
                "ticket_no": ticket.ticket_no,
                "title": ticket.title,
                "description": ticket.description,
                "category": ticket.category,
                "priority": ticket.priority.value if hasattr(ticket.priority, "value") else str(ticket.priority),
                "status": ticket.status,
                "department": ticket.department,
                "created_at": ticket.created_at.isoformat() if ticket.created_at else None,
                "resolved_at": ticket.resolved_at.isoformat() if ticket.resolved_at else None,
                "closed_at": ticket.closed_at.isoformat() if ticket.closed_at else None,
                "resolution_notes": ticket.resolution_notes,
                "ai_summary": ticket.ai_summary,
                "similarity": sim,
                "created_by": detail.get("created_by"),
            })

    scored.sort(key=lambda x: x["similarity"], reverse=True)
    return scored[:limit]
