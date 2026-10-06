"""Server-Sent Events stream for live per-user updates.

Connected clients receive notifications (and related ticket events) the moment
they are created. A heartbeat comment is emitted every 25s to keep
proxies/browsers from closing idle connections.
"""
from __future__ import annotations

import asyncio
import json
from typing import AsyncIterator

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.core.deps import get_current_user
from app.models.user import User
from app.services.event_hub import event_hub

router = APIRouter(prefix="/events", tags=["events"])

_HEARTBEAT_SECONDS = 25.0


async def _stream(user_id: str) -> AsyncIterator[str]:
    async for event in event_hub.stream(user_id, heartbeat=_HEARTBEAT_SECONDS):
        if event is None:
            yield ": heartbeat\n\n"
            continue
        yield f"data: {json.dumps(event)}\n\n"


@router.get("")
async def events(user: User = Depends(get_current_user)) -> StreamingResponse:
    return StreamingResponse(
        _stream(user.id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )