"""In-memory event hub for real-time Server-Sent Events.

A single shared hub fans out JSON events to every live SSE subscriber for a
user. ``publish`` is thread-safe (safe to call from sync FastAPI handlers via
``loop.call_soon_threadsafe``); ``stream`` is an async generator consumed by
the SSE endpoint.
"""
from __future__ import annotations

import asyncio
import threading
from collections import defaultdict
from typing import AsyncIterator, Dict, Set

_STREAM_SIZE = 100


class EventHub:
    def __init__(self) -> None:
        self._queues: Dict[str, Set[asyncio.Queue]] = defaultdict(set)
        self._lock = threading.Lock()
        self.loop: asyncio.AbstractEventLoop | None = None

    def bind_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        self.loop = loop

    def publish(self, user_id: str, event: dict) -> None:
        if self.loop is None:
            return
        with self._lock:
            subscribers = list(self._queues.get(user_id, ()))
        for queue in subscribers:
            self.loop.call_soon_threadsafe(queue.put_nowait, event)

    async def stream(
        self, user_id: str, heartbeat: float | None = None
    ) -> AsyncIterator[dict | None]:
        """Yield events for a user.

        If ``heartbeat`` seconds elapse with no event, ``None`` is yielded so the
        SSE endpoint can emit a keep-alive comment.
        """
        queue: asyncio.Queue = asyncio.Queue(maxsize=_STREAM_SIZE)
        with self._lock:
            self._queues[user_id].add(queue)
        try:
            while True:
                try:
                    if heartbeat is not None:
                        event = await asyncio.wait_for(queue.get(), timeout=heartbeat)
                    else:
                        event = await queue.get()
                except asyncio.TimeoutError:
                    yield None
                    continue
                except asyncio.CancelledError:
                    break
                yield event
        finally:
            with self._lock:
                self._queues[user_id].discard(queue)
                if not self._queues[user_id]:
                    self._queues.pop(user_id, None)


event_hub = EventHub()