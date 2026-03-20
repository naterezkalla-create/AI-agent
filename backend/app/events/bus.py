"""Lightweight in-process event bus for realtime UI updates."""

from __future__ import annotations

import asyncio
from collections.abc import Iterable
from datetime import datetime, timezone
from typing import Any


EventPayload = dict[str, Any]


class EventBus:
    """Broadcast platform events to long-lived subscribers."""

    def __init__(self) -> None:
        self._subscribers: dict[asyncio.Queue[EventPayload], set[str] | None] = {}
        self._lock = asyncio.Lock()

    async def subscribe(self, topics: Iterable[str] | None = None) -> asyncio.Queue[EventPayload]:
        queue: asyncio.Queue[EventPayload] = asyncio.Queue()
        normalized = {topic.strip() for topic in topics or [] if topic.strip()} or None
        async with self._lock:
            self._subscribers[queue] = normalized
        return queue

    async def unsubscribe(self, queue: asyncio.Queue[EventPayload]) -> None:
        async with self._lock:
            self._subscribers.pop(queue, None)

    async def publish(
        self,
        event_type: str,
        payload: dict[str, Any],
        *,
        user_id: str = "default",
        topics: Iterable[str] | None = None,
    ) -> EventPayload:
        event_topics = {topic.strip() for topic in topics or [] if topic.strip()}
        event_topics.add(event_type.split(".", 1)[0])

        event = {
            "type": event_type,
            "payload": payload,
            "user_id": user_id,
            "topics": sorted(event_topics),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        async with self._lock:
            subscribers = list(self._subscribers.items())

        for queue, subscriber_topics in subscribers:
            if subscriber_topics and not (event_topics & subscriber_topics):
                continue
            queue.put_nowait(event)

        return event


event_bus = EventBus()

