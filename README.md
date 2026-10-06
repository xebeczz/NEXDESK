# NEXDESK — AI-Based Smart IT Ticket Management System

A production-ready, full-stack helpdesk platform with an **NVIDIA AI assistant** that
converses with employees, detects intent, troubleshoots, and proposes tickets —
never creating them directly. Real-time SSE updates, role-based access, live
analytics, SLA tracking, and generated PDF reports.

| Layer | Stack |
| --- | --- |
| Frontend | React 19 · Vite · TypeScript · Tailwind v4 · shadcn/ui · TanStack Query · React Router · Axios · Framer Motion · Recharts · react-markdown |
| Backend | FastAPI · SQLAlchemy 2.x · Alembic · Pydantic v2 · JWT (access + refresh) · bcrypt · ReportLab |
| AI | NVIDIA AI model via OpenAI-compatible API (`integrate.api.nvidia.com/v1`) — **key lives only in the backend `.env`, never sent to the frontend** |
| Data | SQLite for dev (file-based, zero-config) · PostgreSQL-ready via `DATABASE_URL` |
| Realtime | Server-Sent Events (`/api/v1/events`) — live notifications & refresh, no polling |
| Deployment | Docker Compose (backend container + nginx-served frontend) |

## Roles & permissions

| Role | Can do |
| --- | --- |
| **Admin** | Everything — all tickets, user management, system health, audit logs, delete tickets, all reports |
| **User** | Create/view their own tickets, upload attachments, comment, use the AI assistant, confirm AI-proposed drafts |

Password reset emails are logged to the backend console in dev (no SMTP
configured); set `SMTP_*` env vars for production delivery.

## Getting started (local development)

### 1. Backend

```bash
cd backend
python -m venv .venv                  # Python 3.11+
.venv\Scripts\activate                # (Windows)  source .venv/bin/activate (macOS/Linux)
pip install -r requirements.txt
cp .env.example .env                  # edit SECRET_KEY; add NVIDIA_API_KEY to enable the AI model
alembic upgrade head                  # create schema
python seed.py --with-sample-tickets  # seed admin/user + sample data
uvicorn app.main:app --reload         # http://127.0.0.1:8000  (docs at /docs)
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev                           # http://localhost:5173  (proxies /api → backend)
```

## Seed credentials

| Role | Email | Password |
| --- | --- | --- |
| Admin | `admin@itdesk.io` | `Admin@12345` |
| User | `user@itdesk.io` | `User@12345` |

## NVIDIA AI integration

Set `NVIDIA_API_KEY` in `backend/.env` to enable the hosted AI model
(`NVIDIA_MODEL`, default `nvidia/nemotron-3-ultra-550b-a55b`). The backend calls
`NVIDIA_BASE_URL` (`https://integrate.api.nvidia.com/v1`) with httpx and streams
replies to the chat as SSE.

**Without a key, the app runs in fully-functional offline fallback mode** — a
deterministic rule-based engine handles intent detection, troubleshooting
answers, and ticket-draft proposals, so every feature still works for testing.

**How tickets get created (safety by design):** the AI never creates a ticket
directly. Every turn is validated on the backend into structured JSON
(`intent, priority, category, department, should_create_ticket`), Pydantic-validated
**before** any persistence. A draft is saved and shown to the user, who must
explicitly confirm it. Greetings, smalltalk, and normal troubleshooting never
reach ticket creation.

## Docker Compose

Docker files are provided and ready to run (requires Docker Engine):

```bash
cp backend/.env.example backend/.env   # set SECRET_KEY (+ NVIDIA_API_KEY if desired)
docker compose up --build
# Frontend → http://localhost:8080
# Backend  → http://localhost:8000/docs

# Optionally seed demo users + sample tickets (the image starts with an empty DB):
docker compose exec backend python seed.py --with-sample-tickets
```

The backend container runs `alembic upgrade head` on startup and persists its
SQLite database and uploads in named volumes. `proxy_buffering off` in nginx
lets the SSE event stream flow through to the browser untouched. `.dockerignore`
files keep dev artifacts (local SQLite data, uploads, `.env`) out of the image,
so each fresh volume starts clean and gets its own seeded data.

## Testing

```bash
cd backend
pytest -q            # 38 tests: auth/RBAC, ticket workflow, AI rules, analytics role-scoping
```

## Key API surface

- `POST /api/v1/auth/register | login | refresh | logout | forgot-password | reset-password`, `GET /me`
- `/api/v1/tickets` — CRUD, search/filter/paginate, assign/transfer, close/reopen, comments, activities, attachments, per-ticket PDF
- `/api/v1/chat/sessions` — sessioned AI chat, streaming SSE, persisted history, ticket drafts (`confirm`/`dismiss`)
- `/api/v1/dashboard/stats`, `/api/v1/analytics/*` — real SQL aggregates, role-scoped
- `/api/v1/admin/*` — users, system health, recent activity, audit logs
- `/api/v1/events` — per-user SSE stream (live notifications)
- `/api/v1/reports/{summary,analytics,resolution,priority,monthly}` — ReportLab PDFs

## Recent fixes (stabilization)

- **Role-based navigation**: Sidebar now conditionally renders items based on `user.role` (User sees Dashboard, My Tickets, AI Assistant, Reports, Settings; Admin sees all including All Tickets, Users, System)
- **Route protection**: `/tickets`, `/admin/users`, `/admin/system` wrapped with `RoleRoute` — Users redirected, Admins allowed
- **Select placeholder fix**: Empty Status/Priority filter dropdowns now show "Status" / "Priority" placeholders correctly (was `""` instead of `undefined`)
- **Selected value visibility**: All Select components (Status, Priority, Role, Assignee) display selected values correctly
- **Admin registration code**: Configurable via `ADMIN_REGISTRATION_CODE` in `.env` (empty in `.env.example`)
- **PDF report downloads**: All 5 report types generate valid PDFs via ReportLab, authenticated Admin-only
- **AI Assistant auth**: Fixed missing `getAccessToken` import for streaming requests

## Project structure

```
backend/            FastAPI app (app/api, app/services, app/models, app/schemas),
                    alembic migrations, seed.py, pytest suite
frontend/           Vite React app (src/pages, src/components, src/hooks,
                    src/providers, src/api), Tailwind, shadcn/ui
docker-compose.yml  Backend + frontend orchestration
```
README.md
Displaying README.md.
