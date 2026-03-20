"""Realtime event streaming endpoints."""

from __future__ import annotations

import asyncio
import json
from collections.abc import Iterable

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.api.deps import get_current_user
from app.events.bus import event_bus

router = APIRouter(prefix="/api/realtime", tags=["realtime"])


def _parse_topics(raw_topics: str | None) -> list[str]:
    if not raw_topics:
        return []
    return [topic.strip() for topic in raw_topics.split(",") if topic.strip()]


@router.get("/events")
async def stream_events(topics: str | None = None, user_id: str = Depends(get_current_user)):
    """Stream app events over server-sent events."""

    async def event_generator(parsed_topics: Iterable[str]):
        queue = await event_bus.subscribe(parsed_topics)

        try:
            # Initial handshake event so clients can render "connected" state.
            yield f"data: {json.dumps({'type': 'realtime.connected', 'payload': {'user_id': user_id}})}\n\n"

            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=20)
                    if event.get("user_id") not in {user_id, "all"}:
                        continue
                    yield f"data: {json.dumps(event)}\n\n"
                except asyncio.TimeoutError:
                    yield ": keep-alive\n\n"
        finally:
            await event_bus.unsubscribe(queue)

    return StreamingResponse(
        event_generator(_parse_topics(topics)),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
