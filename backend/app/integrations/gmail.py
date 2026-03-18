"""Gmail API wrapper — send emails, list inbox."""

import base64
import logging
from typing import Optional
from email.mime.text import MIMEText
import httpx
from app.integrations.oauth import get_access_token

logger = logging.getLogger(__name__)

GMAIL_API = "https://gmail.googleapis.com/gmail/v1/users/me"


async def _get_headers(user_id: str) -> Optional[dict]:
    token = await get_access_token(user_id, "google")
    if not token:
        return None
    return {"Authorization": f"Bearer {token}"}


async def send_email(user_id: str, to: str, subject: str, body: str) -> str:
    headers = await _get_headers(user_id)
    if not headers:
        return "Gmail not connected. Please connect your Google account first."

    message = MIMEText(body)
    message["to"] = to
    message["subject"] = subject
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            f"{GMAIL_API}/messages/send",
            headers=headers,
            json={"raw": raw},
        )

    if response.status_code == 200:
        return f"Email sent to {to} with subject '{subject}'"
    else:
        return f"Failed to send email: {response.status_code} {response.text}"


async def list_inbox(user_id: str, max_results: int = 10, query: str = "") -> str:
    headers = await _get_headers(user_id)
    if not headers:
        return "Gmail not connected. Please connect your Google account first."

    params = {"maxResults": max_results}
    if query:
        params["q"] = query

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(
            f"{GMAIL_API}/messages",
            headers=headers,
            params=params,
        )

        if response.status_code != 200:
            return f"Failed to list inbox: {response.status_code}"

        data = response.json()
        messages = data.get("messages", [])

        if not messages:
            return "No messages found."

        results = []
        for msg_ref in messages[:max_results]:
            msg_response = await client.get(
                f"{GMAIL_API}/messages/{msg_ref['id']}",
                headers=headers,
                params={"format": "metadata", "metadataHeaders": ["Subject", "From", "Date"]},
            )
            if msg_response.status_code != 200:
                continue

            msg_data = msg_response.json()
            headers_list = msg_data.get("payload", {}).get("headers", [])
            header_map = {h["name"]: h["value"] for h in headers_list}

            results.append(
                f"From: {header_map.get('From', 'Unknown')}\n"
                f"Subject: {header_map.get('Subject', '(no subject)')}\n"
                f"Date: {header_map.get('Date', 'Unknown')}\n"
                f"ID: {msg_ref['id']}"
            )

    return "\n---\n".join(results) if results else "No messages found."
