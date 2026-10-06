"""FastAPI application entrypoint."""
from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1 import admin, analytics, auth, chat, dashboard, events, notifications, reports, settings as settings_router, tickets
from app.core.config import settings
from app.services.event_hub import event_hub


import os
import app.models  # Ensures all ORM models are registered
from app.db.base import Base
from app.db.session import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create data directory if using SQLite file database
    if settings.DATABASE_URL.startswith("sqlite"):
        os.makedirs("./data", exist_ok=True)
    # Ensure database tables exist automatically on startup
    Base.metadata.create_all(bind=engine)

    # Bind the running loop so sync handlers can push real-time events safely.
    event_hub.bind_loop(asyncio.get_running_loop())
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    debug=settings.DEBUG,
    lifespan=lifespan,
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    print(f"[DEBUG] 422 Validation error for {request.url.path}: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
    )


# CORS — restricted to configured frontend origin(s).
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_V1 = "/api/v1"
app.include_router(auth.router, prefix=API_V1)
app.include_router(tickets.router, prefix=API_V1)
app.include_router(chat.router, prefix=API_V1)
app.include_router(dashboard.router, prefix=API_V1)
app.include_router(analytics.router, prefix=API_V1)
app.include_router(admin.router, prefix=API_V1)
app.include_router(notifications.router, prefix=API_V1)
app.include_router(events.router, prefix=API_V1)
app.include_router(reports.router, prefix=API_V1)
app.include_router(settings_router.router, prefix=API_V1)


@app.get("/", tags=["system"])
def root():
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/docs")


@app.get("/health", tags=["system"])
def health_check() -> dict:
    return {"status": "ok", "app": settings.APP_NAME, "env": settings.APP_ENV}