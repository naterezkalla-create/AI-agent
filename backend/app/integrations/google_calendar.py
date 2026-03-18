"""Google Calendar API wrapper."""

import logging
from datetime import datetime, timezone
from typing import Optional
import httpx
from app.integrations.oauth import get_access_token

logger = logging.getLogger(__name__)

CALENDAR_API = "https://www.googleapis.com/calendar/v3"


async def _get_headers(user_id: str) -> Optional[dict]:
    token = await get_access_token(user_id, "google")
    if not token:
        return None
    return {"Authorization": f"Bearer {token}"}


async def create_event(
    user_id: str,
    title: str,
    start_time: str,
    end_time: str,
    description: str = "",
    location: str = "",
) -> str:
    headers = await _get_headers(user_id)
    if not headers:
        return "Google Calendar not connected. Please connect your Google account first."

    event_body = {
        "summary": title,
        "start": {"dateTime": start_time},
        "end": {"dateTime": end_time},
    }
    if description:
        event_body["description"] = description
    if location:
        event_body["location"] = location

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            f"{CALENDAR_API}/calendars/primary/events",
            headers=headers,
            json=event_body,
        )

    if response.status_code == 200:
        event = response.json()
        return f"Event created: '{title}' on {start_time} (ID: {event.get('id', 'unknown')})"
    else:
        return f"Failed to create event: {response.status_code} {response.text}"


async def list_events(
    user_id: str,
    max_results: int = 10,
    time_min: str = "",
) -> str:
    headers = await _get_headers(user_id)
    if not headers:
        return "Google Calendar not connected. Please connect your Google account first."

    if not time_min:
        time_min = datetime.now(timezone.utc).isoformat()

    params = {
        "maxResults": max_results,
        "timeMin": time_min,
        "singleEvents": "true",
        "orderBy": "startTime",
    }

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(
            f"{CALENDAR_API}/calendars/primary/events",
            headers=headers,
            params=params,
        )

    if response.status_code != 200:
        return f"Failed to list events: {response.status_code}"

    data = response.json()
    events = data.get("items", [])

    if not events:
        return "No upcoming events found."

    results = []
    for event in events:
        start = event.get("start", {}).get("dateTime", event.get("start", {}).get("date", "Unknown"))
        results.append(
            f"📅 {event.get('summary', '(No title)')}\n"
            f"   When: {start}\n"
            f"   Where: {event.get('location', 'N/A')}\n"
            f"   ID: {event.get('id', 'unknown')}"
        )

    return "\n\n".join(results)
