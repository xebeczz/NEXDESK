import os
import json
import sqlite3
import re
from functools import wraps

import requests
from dotenv import load_dotenv
from flask import Flask, request, jsonify, session, render_template, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash


# ============================================================
# Environment Configuration
# ============================================================

load_dotenv()


# ============================================================
# Flask Application
# ============================================================

app = Flask(
    __name__,
    static_folder="static",
    template_folder="templates"
)

app.secret_key = os.environ.get(
    "SECRET_KEY",
    "dev-only-change-this-in-production"
)


# ============================================================
# Database Configuration
# ============================================================
#
# Vercel serverless functions have a read-only deployment
# filesystem. /tmp is writable but temporary.
#
# For local development:
#     database.db
#
# On Vercel:
#     /tmp/support_ai_ticket_management.db
#
# IMPORTANT:
# SQLite stored in /tmp is NOT permanent on Vercel.
# For production persistence, use PostgreSQL/Neon later.
# ============================================================

if os.environ.get("VERCEL"):
    DB_FILE = "/tmp/support_ai_ticket_management.db"
else:
    DB_FILE = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "database.db"
    )


# ============================================================
# Gemini Configuration
# ============================================================

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

GEMINI_MODEL_NAME = os.environ.get(
    "GEMINI_MODEL",
    "gemini-2.5-flash"
)

GEMINI_API_BASE = (
    "https://generativelanguage.googleapis.com/v1beta"
)

# Keep this below the Vercel function timeout.
GEMINI_TIMEOUT = 45


# ============================================================
# AI Prompts
# ============================================================

CHAT_SYSTEM_PROMPT = (
    "You are the AI Agent inside 'AI Support Desk', an internal IT support tool. "
    "Help the user troubleshoot hardware, software, credentials, and operational issues. "
    "Be concise and practical, and suggest raising a ticket when the issue can't be resolved directly in chat."
)


TICKET_ANALYSIS_PROMPT = (
    "You are the ticket-triage assistant inside 'AI Support Desk'. Given a ticket's subject and "
    "description, respond with ONLY a JSON object (no markdown fences, no extra text) with these keys:\n"
    '  "category": a short category like "Hardware", "Software", "Credentials", "Network", or "Other"\n'
    '  "priority": one of "High", "Medium", "Low"\n'
    '  "summary": one or two sentences summarizing the likely cause\n'
    '  "recommendation": 2-4 short suggested troubleshooting steps, as a single string with steps separated by newlines\n'
)


# ============================================================
# Gemini Helper Functions
# ============================================================

def _history_to_gemini_contents(history):
    """
    Converts sqlite3.Row / dict rows shaped like:
    {'role': 'user'|'assistant', 'message': str}

    into Gemini REST contents format:
    {'role': 'user'|'model', 'parts': [{'text': ...}]}
    """

    contents = []

    for turn in history or []:
        role = "model" if turn["role"] == "assistant" else "user"

        contents.append({
            "role": role,
            "parts": [
                {
                    "text": turn["message"]
                }
            ]
        })

    return contents


def _extract_gemini_error(response):
    """
    Gemini REST errors usually come back as:
    {
        "error": {
            "message": "...",
            "status": "..."
        }
    }
    """

    try:
        body = response.json()

        message = body.get("error", {}).get("message")

        if message:
            return message

    except ValueError:
        pass

    return (
        response.text.strip()[:300]
        or f"HTTP {response.status_code}"
    )


def _call_gemini(system_prompt, contents):
    """
    Low-level call to Gemini's generateContent endpoint.

    Returns:
        (text, error)
    """

    if not GEMINI_API_KEY:
        return None, (
            "No Gemini API key is configured. "
            "Set GEMINI_API_KEY in your Vercel Environment Variables."
        )

    url = (
        f"{GEMINI_API_BASE}/models/"
        f"{GEMINI_MODEL_NAME}:generateContent"
    )

    payload = {
        "system_instruction": {
            "parts": [
                {
                    "text": system_prompt
                }
            ]
        },
        "contents": contents
    }

    try:
        response = requests.post(
            url,
            params={
                "key": GEMINI_API_KEY
            },
            json=payload,
            timeout=GEMINI_TIMEOUT
        )

        # ----------------------------------------------------
        # Gemini Error Handling
        # ----------------------------------------------------

        if response.status_code == 400:
            return None, (
                "Gemini rejected the request: "
                f"{_extract_gemini_error(response)}"
            )

        if response.status_code == 403:
            return None, (
                "Gemini rejected the API key: "
                "it's invalid, restricted, or lacks access to this model."
            )

        if response.status_code == 404:
            return None, (
                f"Model '{GEMINI_MODEL_NAME}' was not found. "
                "Check the GEMINI_MODEL environment variable."
            )

        if response.status_code == 429:
            return None, (
                "Gemini rate limit or quota exceeded. "
                "Please wait a moment and try again."
            )

        response.raise_for_status()

        data = response.json()

        candidates = data.get("candidates", [])

        if not candidates:
            block_reason = (
                data.get("promptFeedback", {})
                .get("blockReason")
            )

            if block_reason:
                return None, (
                    f"Gemini blocked this request ({block_reason})."
                )

            return None, "The model returned an empty response."

        parts = (
            candidates[0]
            .get("content", {})
            .get("parts", [])
        )

        text = "".join(
            p.get("text", "")
            for p in parts
        ).strip()

        return (
            text or None,
            None if text else "The model returned an empty response."
        )

    except requests.exceptions.ConnectionError:
        return None, (
            "Could not reach the Gemini API. "
            "Please check the API configuration."
        )

    except requests.exceptions.Timeout:
        return None, (
            "The request to Gemini timed out. "
            "Please try again."
        )

    except requests.exceptions.HTTPError as e:
        detail = (
            _extract_gemini_error(e.response)
            if e.response is not None
            else str(e)
        )

        return None, f"Gemini API error: {detail}"

    except Exception as e:
        return None, (
            f"Unexpected error while contacting Gemini: {e}"
        )


def query_gemini(user_message, history=None):
    """
    Chat call used by the AI Agent page.

    Always returns user-facing text.
    """

    contents = (
        _history_to_gemini_contents(history)
        + [
            {
                "role": "user",
                "parts": [
                    {
                        "text": user_message
                    }
                ]
            }
        ]
    )

    text, error = _call_gemini(
        CHAT_SYSTEM_PROMPT,
        contents
    )

    return text if text else f"⚠️ {error}"


def analyze_ticket_with_gemini(title, description):
    """
    Ticket-triage call used by Raise Ticket.

    Returns:
        category
        priority
        summary
        recommendation

    Falls back to sane defaults if Gemini isn't configured
    or the response can't be parsed.
    """

    fallback = {
        "category": "Other",
        "priority": "Medium",
        "summary": (
            "Automatic analysis is unavailable right now, "
            "so this ticket has been queued for manual review."
        ),
        "recommendation": (
            "A member of the support team will review "
            "this ticket shortly."
        )
    }

    user_message = (
        f"Ticket subject: {title}\n\n"
        f"Description:\n{description}"
    )

    contents = [
        {
            "role": "user",
            "parts": [
                {
                    "text": user_message
                }
            ]
        }
    ]

    text, error = _call_gemini(
        TICKET_ANALYSIS_PROMPT,
        contents
    )

    if not text:
        fallback["summary"] = (
            f"⚠️ {error} "
            "This ticket has been queued for manual review."
        )

        return fallback

    # Gemini can sometimes wrap JSON in markdown fences.
    cleaned = re.sub(
        r"^```(?:json)?|```$",
        "",
        text.strip(),
        flags=re.MULTILINE
    ).strip()

    try:
        parsed = json.loads(cleaned)

        priority = parsed.get(
            "priority",
            "Medium"
        )

        if priority not in (
            "High",
            "Medium",
            "Low"
        ):
            priority = "Medium"

        return {
            "category": (
                parsed.get("category", "Other")
                or "Other"
            ),
            "priority": priority,
            "summary": (
                parsed.get(
                    "summary",
                    fallback["summary"]
                )
                or fallback["summary"]
            ),
            "recommendation": (
                parsed.get(
                    "recommendation",
                    fallback["recommendation"]
                )
                or fallback["recommendation"]
            )
        }

    except (ValueError, AttributeError):
        # Model did not return clean JSON.
        # Keep the response rather than losing it.
        fallback["summary"] = cleaned[:500]

        return fallback


# ============================================================
# Database Helper Functions
# ============================================================

def get_db_connection():
    """
    Create a SQLite connection.
    """

    conn = sqlite3.connect(DB_FILE)

    conn.row_factory = sqlite3.Row

    return conn


def init_db():
    """
    Initialize the SQLite database and tables.
    """

    # --------------------------------------------------------
    # Check whether an existing database is valid.
    # --------------------------------------------------------

    if os.path.exists(DB_FILE):
        try:
            with sqlite3.connect(DB_FILE) as conn:
                conn.execute(
                    "SELECT name FROM sqlite_master LIMIT 1"
                )

        except sqlite3.DatabaseError:

            try:
                os.remove(DB_FILE)
            except OSError:
                pass

    # --------------------------------------------------------
    # Create database tables.
    # --------------------------------------------------------

    with get_db_connection() as conn:

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                email TEXT
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                role TEXT NOT NULL,
                message TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                employee_name TEXT NOT NULL,
                employee_id TEXT,
                department TEXT,
                title TEXT NOT NULL,
                description TEXT,
                priority TEXT DEFAULT 'Medium',
                status TEXT DEFAULT 'Open',
                ai_summary TEXT,
                ai_recommendation TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS user_settings (
                user_id INTEGER PRIMARY KEY,
                email_alerts INTEGER DEFAULT 1,
                keep_chat_history INTEGER DEFAULT 1,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
            """
        )

        conn.commit()


# Initialize database when Flask starts.
init_db()


# ============================================================
# Authentication Decorators
# ============================================================

def login_required_page(view_func):
    """
    Redirect unauthenticated page requests to login.
    """

    @wraps(view_func)
    def wrapped(*args, **kwargs):

        if "user_id" not in session:
            return redirect(
                url_for("login_page")
            )

        return view_func(*args, **kwargs)

    return wrapped


def login_required_api(view_func):
    """
    Return JSON 401 for API requests.
    """

    @wraps(view_func)
    def wrapped(*args, **kwargs):

        if "user_id" not in session:
            return jsonify({
                "error": "Unauthorized"
            }), 401

        return view_func(*args, **kwargs)

    return wrapped


# ============================================================
# Template Context
# ============================================================

@app.context_processor
def inject_current_user():

    username = session.get("username")

    initials = (
        "".join(
            [
                part[0].upper()
                for part in username.split()
                if part
            ]
        )[:2]
        if username
        else "JD"
    )

    return {
        "current_username": username or "Guest",
        "current_initials": initials,
        "current_role": session.get(
            "role",
            "Account User"
        )
    }


# ============================================================
# Health Check
# ============================================================

@app.route("/health", methods=["GET"])
def health():
    """
    Simple endpoint to verify that the Vercel
    serverless function is running.
    """

    return jsonify({
        "status": "ok",
        "service": "AI Support Desk"
    }), 200


# ============================================================
# Page Routes
# ============================================================

@app.route("/")
def serve_index():

    if "user_id" in session:
        return redirect(
            url_for("dashboard_page")
        )

    return redirect(
        url_for("login_page")
    )


@app.route("/login")
def login_page():

    if "user_id" in session:
        return redirect(
            url_for("dashboard_page")
        )

    return render_template("login.html")


@app.route("/register")
def register_page():

    if "user_id" in session:
        return redirect(
            url_for("dashboard_page")
        )

    return render_template("register.html")


@app.route("/dashboard")
@login_required_page
def dashboard_page():

    return render_template(
        "dashboard.html"
    )


@app.route("/raise-ticket")
@login_required_page
def raise_ticket_page():

    return render_template(
        "raise_ticket.html"
    )


@app.route("/open-tickets")
@login_required_page
def open_tickets_page():

    return render_template(
        "open_tickets.html"
    )


@app.route("/ai-agent")
@login_required_page
def ai_agent_page():

    return render_template(
        "ai_agent.html"
    )


@app.route("/about")
@login_required_page
def about_page():

    return render_template(
        "about.html"
    )


@app.route("/settings")
@login_required_page
def settings_page():

    return render_template(
        "settings.html"
    )


# ============================================================
# Authentication APIs
# ============================================================

@app.route(
    "/api/auth/signup",
    methods=["POST"]
)
def signup():

    data = request.json or {}

    username = data.get("username")
    password = data.get("password")
    email = data.get("email")

    if not username or not password:
        return jsonify({
            "error": "Missing username or password"
        }), 400

    if len(password) < 6:
        return jsonify({
            "error": "Password must be at least 6 characters"
        }), 400

    hashed_password = generate_password_hash(
        password
    )

    try:

        with get_db_connection() as conn:

            cur = conn.execute(
                """
                INSERT INTO users
                (username, password, email)
                VALUES (?, ?, ?)
                """,
                (
                    username,
                    hashed_password,
                    email
                )
            )

            conn.execute(
                """
                INSERT INTO user_settings
                (user_id)
                VALUES (?)
                """,
                (cur.lastrowid,)
            )

            conn.commit()

        return jsonify({
            "message": "User registered successfully!"
        }), 201

    except sqlite3.IntegrityError:

        return jsonify({
            "error": "Username already exists"
        }), 400


@app.route(
    "/api/auth/login",
    methods=["POST"]
)
def login():

    data = request.json or {}

    username = data.get("username")
    password = data.get("password")

    with get_db_connection() as conn:

        user = conn.execute(
            """
            SELECT *
            FROM users
            WHERE username = ?
               OR email = ?
            """,
            (
                username,
                username
            )
        ).fetchone()

    if user and check_password_hash(
        user["password"],
        password
    ):

        session["user_id"] = user["id"]
        session["username"] = user["username"]
        session["role"] = "Account User"

        return jsonify({
            "message": "Login successful",
            "username": user["username"]
        }), 200

    return jsonify({
        "error": "Invalid credentials"
    }), 401


@app.route(
    "/api/auth/logout",
    methods=["POST"]
)
def logout():

    session.clear()

    return jsonify({
        "message": "Logged out successfully"
    }), 200


# ============================================================
# Dashboard API
# ============================================================

@app.route(
    "/api/dashboard/stats",
    methods=["GET"]
)
@login_required_api
def dashboard_stats():

    with get_db_connection() as conn:

        total = conn.execute(
            "SELECT COUNT(*) c FROM tickets"
        ).fetchone()["c"]

        open_count = conn.execute(
            """
            SELECT COUNT(*) c
            FROM tickets
            WHERE status = 'Open'
            """
        ).fetchone()["c"]

        in_progress = conn.execute(
            """
            SELECT COUNT(*) c
            FROM tickets
            WHERE status = 'In Progress'
            """
        ).fetchone()["c"]

        resolved = conn.execute(
            """
            SELECT COUNT(*) c
            FROM tickets
            WHERE status = 'Resolved'
            """
        ).fetchone()["c"]

        recent = conn.execute(
            """
            SELECT
                id,
                title,
                department,
                priority,
                status,
                created_at
            FROM tickets
            ORDER BY created_at DESC
            LIMIT 5
            """
        ).fetchall()

    return jsonify({
        "total": total,
        "open": open_count,
        "in_progress": in_progress,
        "resolved": resolved,
        "recent": [
            dict(row)
            for row in recent
        ]
    }), 200


# ============================================================
# Ticket APIs
# ============================================================

@app.route(
    "/api/tickets",
    methods=["GET", "POST"]
)
@login_required_api
def handle_tickets():

    user_id = session["user_id"]

    # --------------------------------------------------------
    # Create Ticket
    # --------------------------------------------------------

    if request.method == "POST":

        data = request.json or {}

        title = (
            data.get("title") or ""
        ).strip()

        description = (
            data.get("description") or ""
        ).strip()

        employee_name = (
            data.get("employee_name") or ""
        ).strip()

        if (
            not title
            or not description
            or not employee_name
        ):

            return jsonify({
                "error": (
                    "Employee name, subject, "
                    "and description are required"
                )
            }), 400

        employee_id = data.get(
            "employee_id",
            ""
        )

        department = data.get(
            "department",
            "Engineering"
        )

        # ----------------------------------------------------
        # AI Ticket Analysis
        # ----------------------------------------------------

        analysis = analyze_ticket_with_gemini(
            title,
            description
        )

        # ----------------------------------------------------
        # Store Ticket
        # ----------------------------------------------------

        with get_db_connection() as conn:

            cur = conn.execute(
                """
                INSERT INTO tickets
                (
                    user_id,
                    employee_name,
                    employee_id,
                    department,
                    title,
                    description,
                    priority,
                    status,
                    ai_summary,
                    ai_recommendation
                )
                VALUES
                (
                    ?, ?, ?, ?, ?, ?, ?, 'Open', ?, ?
                )
                """,
                (
                    user_id,
                    employee_name,
                    employee_id,
                    department,
                    title,
                    description,
                    analysis["priority"],
                    analysis["summary"],
                    analysis["recommendation"]
                )
            )

            conn.commit()

            ticket = conn.execute(
                """
                SELECT *
                FROM tickets
                WHERE id = ?
                """,
                (cur.lastrowid,)
            ).fetchone()

        return jsonify(
            dict(ticket)
        ), 201

    # --------------------------------------------------------
    # Get Tickets
    # --------------------------------------------------------

    with get_db_connection() as conn:

        tickets = conn.execute(
            """
            SELECT *
            FROM tickets
            ORDER BY created_at DESC
            """
        ).fetchall()

    return jsonify([
        dict(ticket)
        for ticket in tickets
    ]), 200


@app.route(
    "/api/tickets/<int:ticket_id>",
    methods=["GET", "PATCH"]
)
@login_required_api
def handle_ticket_detail(ticket_id):

    with get_db_connection() as conn:

        ticket = conn.execute(
            """
            SELECT *
            FROM tickets
            WHERE id = ?
            """,
            (ticket_id,)
        ).fetchone()

        if not ticket:

            return jsonify({
                "error": "Ticket not found"
            }), 404

        # ----------------------------------------------------
        # Update Ticket Status
        # ----------------------------------------------------

        if request.method == "PATCH":

            data = request.json or {}

            status = data.get("status")

            if status not in (
                "Open",
                "In Progress",
                "Resolved"
            ):

                return jsonify({
                    "error": "Invalid status"
                }), 400

            conn.execute(
                """
                UPDATE tickets
                SET
                    status = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (
                    status,
                    ticket_id
                )
            )

            conn.commit()

            ticket = conn.execute(
                """
                SELECT *
                FROM tickets
                WHERE id = ?
                """,
                (ticket_id,)
            ).fetchone()

    return jsonify(
        dict(ticket)
    ), 200


# ============================================================
# Settings APIs
# ============================================================

@app.route(
    "/api/settings",
    methods=["GET", "PUT"]
)
@login_required_api
def handle_settings():

    user_id = session["user_id"]

    # --------------------------------------------------------
    # Update Settings
    # --------------------------------------------------------

    if request.method == "PUT":

        data = request.json or {}

        with get_db_connection() as conn:

            conn.execute(
                """
                INSERT INTO user_settings
                (
                    user_id,
                    email_alerts,
                    keep_chat_history
                )
                VALUES (?, ?, ?)

                ON CONFLICT(user_id)
                DO UPDATE SET
                    email_alerts =
                        excluded.email_alerts,
                    keep_chat_history =
                        excluded.keep_chat_history
                """,
                (
                    user_id,
                    int(
                        bool(
                            data.get(
                                "email_alerts",
                                True
                            )
                        )
                    ),
                    int(
                        bool(
                            data.get(
                                "keep_chat_history",
                                True
                            )
                        )
                    )
                )
            )

            conn.commit()

    # --------------------------------------------------------
    # Get Settings
    # --------------------------------------------------------

    with get_db_connection() as conn:

        row = conn.execute(
            """
            SELECT *
            FROM user_settings
            WHERE user_id = ?
            """,
            (user_id,)
        ).fetchone()

        if not row:

            conn.execute(
                """
                INSERT INTO user_settings
                (user_id)
                VALUES (?)
                """,
                (user_id,)
            )

            conn.commit()

            row = conn.execute(
                """
                SELECT *
                FROM user_settings
                WHERE user_id = ?
                """,
                (user_id,)
            ).fetchone()

    return jsonify({
        "email_alerts": bool(
            row["email_alerts"]
        ),
        "keep_chat_history": bool(
            row["keep_chat_history"]
        )
    }), 200


@app.route(
    "/api/settings/profile",
    methods=["PUT"]
)
@login_required_api
def update_profile():

    data = request.json or {}

    username = (
        data.get("username") or ""
    ).strip()

    if not username:

        return jsonify({
            "error": "Display name cannot be empty"
        }), 400

    try:

        with get_db_connection() as conn:

            conn.execute(
                """
                UPDATE users
                SET username = ?
                WHERE id = ?
                """,
                (
                    username,
                    session["user_id"]
                )
            )

            conn.commit()

        session["username"] = username

        return jsonify({
            "message": "Profile updated",
            "username": username
        }), 200

    except sqlite3.IntegrityError:

        return jsonify({
            "error": "That username is already taken"
        }), 400


@app.route(
    "/api/settings/password",
    methods=["PUT"]
)
@login_required_api
def update_password():

    data = request.json or {}

    password = data.get(
        "password",
        ""
    )

    if len(password) < 6:

        return jsonify({
            "error": (
                "Password must be at least 6 characters"
            )
        }), 400

    with get_db_connection() as conn:

        conn.execute(
            """
            UPDATE users
            SET password = ?
            WHERE id = ?
            """,
            (
                generate_password_hash(password),
                session["user_id"]
            )
        )

        conn.commit()

    return jsonify({
        "message": "Password updated"
    }), 200


# ============================================================
# Chat API
# ============================================================

@app.route(
    "/api/chat",
    methods=["GET", "POST"]
)
@login_required_api
def handle_chat():

    user_id = session["user_id"]

    # --------------------------------------------------------
    # Send Chat Message
    # --------------------------------------------------------

    if request.method == "POST":

        data = request.json or {}

        user_message = data.get(
            "message"
        )

        if not user_message:

            return jsonify({
                "error": "Message required"
            }), 400

        # ----------------------------------------------------
        # Save User Message
        # ----------------------------------------------------

        with get_db_connection() as conn:

            conn.execute(
                """
                INSERT INTO chat_history
                (
                    user_id,
                    role,
                    message
                )
                VALUES (?, ?, ?)
                """,
                (
                    user_id,
                    "user",
                    user_message
                )
            )

            conn.commit()

            # ------------------------------------------------
            # Get Recent Conversation History
            # ------------------------------------------------

            recent_history = conn.execute(
                """
                SELECT
                    role,
                    message
                FROM chat_history
                WHERE user_id = ?
                ORDER BY timestamp DESC
                LIMIT 20
                """,
                (user_id,)
            ).fetchall()

        # Reverse to chronological order and remove
        # the message we just inserted.
        recent_history = (
            list(
                reversed(recent_history)
            )[:-1]
        )

        # ----------------------------------------------------
        # Gemini Response
        # ----------------------------------------------------

        ai_response = query_gemini(
            user_message,
            history=recent_history
        )

        # ----------------------------------------------------
        # Save AI Response
        # ----------------------------------------------------

        with get_db_connection() as conn:

            conn.execute(
                """
                INSERT INTO chat_history
                (
                    user_id,
                    role,
                    message
                )
                VALUES (?, ?, ?)
                """,
                (
                    user_id,
                    "assistant",
                    ai_response
                )
            )

            conn.commit()

        return jsonify({
            "response": ai_response
        }), 200

    # --------------------------------------------------------
    # Get Chat History
    # --------------------------------------------------------

    with get_db_connection() as conn:

        history = conn.execute(
            """
            SELECT
                role,
                message,
                timestamp
            FROM chat_history
            WHERE user_id = ?
            ORDER BY timestamp ASC
            """,
            (user_id,)
        ).fetchall()

    return jsonify([
        dict(row)
        for row in history
    ]), 200


# ============================================================
# Local Development
# ============================================================

if __name__ == "__main__":

    if not GEMINI_API_KEY:

        print(
            "WARNING: GEMINI_API_KEY is not set. "
            "AI ticket analysis and the AI Agent chat "
            "will return a configuration message until it is."
        )

    port = int(
        os.environ.get(
            "PORT",
            5000
        )
    )

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )