"""API wrappers for non-Google integrations."""

from __future__ import annotations

from typing import Any

import httpx

from app.integrations.oauth import get_provider_secret

GITHUB_API = "https://api.github.com"
NOTION_API = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"
SLACK_API = "https://slack.com/api"
APIFY_API = "https://api.apify.com/v2"
RETELL_API = "https://api.retellai.com"


async def _require_secret(user_id: str, provider: str) -> str:
    secret = await get_provider_secret(user_id, provider)
    if not secret:
        raise ValueError(f"{provider} is not connected for this user")
    return secret


async def slack_post_message(user_id: str, channel: str, text: str) -> str:
    token = await _require_secret(user_id, "slack")
    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.post(
            f"{SLACK_API}/chat.postMessage",
            headers={"Authorization": f"Bearer {token}"},
            json={"channel": channel, "text": text},
        )
        payload = response.json()
    if response.status_code != 200 or not payload.get("ok"):
        raise ValueError(payload.get("error", "Slack API request failed"))
    return f"Slack message sent to {channel}."


async def github_list_repos(user_id: str, limit: int = 10) -> list[dict[str, Any]]:
    token = await _require_secret(user_id, "github")
    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.get(
            f"{GITHUB_API}/user/repos",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
            },
            params={"per_page": max(1, min(limit, 50)), "sort": "updated"},
        )
    if response.status_code != 200:
        raise ValueError("GitHub repo lookup failed")
    return [
        {
            "name": repo.get("full_name"),
            "private": repo.get("private"),
            "url": repo.get("html_url"),
            "updated_at": repo.get("updated_at"),
            "description": repo.get("description"),
        }
        for repo in response.json()
    ]


async def github_list_issues(user_id: str, owner: str, repo: str, state: str = "open", limit: int = 10) -> list[dict[str, Any]]:
    token = await _require_secret(user_id, "github")
    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.get(
            f"{GITHUB_API}/repos/{owner}/{repo}/issues",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
            },
            params={"state": state, "per_page": max(1, min(limit, 50))},
        )
    if response.status_code != 200:
        raise ValueError("GitHub issues lookup failed")
    issues = []
    for issue in response.json():
        if issue.get("pull_request"):
            continue
        issues.append(
            {
                "number": issue.get("number"),
                "title": issue.get("title"),
                "state": issue.get("state"),
                "url": issue.get("html_url"),
                "created_at": issue.get("created_at"),
            }
        )
    return issues


async def notion_search(user_id: str, query: str, limit: int = 10) -> list[dict[str, Any]]:
    token = await _require_secret(user_id, "notion")
    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.post(
            f"{NOTION_API}/search",
            headers={
                "Authorization": f"Bearer {token}",
                "Notion-Version": NOTION_VERSION,
            },
            json={"query": query, "page_size": max(1, min(limit, 20))},
        )
    if response.status_code != 200:
        raise ValueError("Notion search failed")
    results = []
    for item in response.json().get("results", []):
        title = ""
        properties = item.get("properties", {})
        if "title" in properties:
            title_parts = properties["title"].get("title", [])
            title = "".join(part.get("plain_text", "") for part in title_parts)
        if not title:
            title_parts = item.get("title", [])
            title = "".join(part.get("plain_text", "") for part in title_parts)
        results.append(
            {
                "id": item.get("id"),
                "object": item.get("object"),
                "title": title or "(untitled)",
                "url": item.get("url"),
            }
        )
    return results


async def notion_create_page(user_id: str, parent_page_id: str, title: str, content: str = "") -> dict[str, Any]:
    token = await _require_secret(user_id, "notion")
    payload: dict[str, Any] = {
        "parent": {"page_id": parent_page_id},
        "properties": {
            "title": {
                "title": [
                    {
                        "type": "text",
                        "text": {"content": title},
                    }
                ]
            }
        },
    }
    if content:
        payload["children"] = [
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": content},
                        }
                    ]
                },
            }
        ]
    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.post(
            f"{NOTION_API}/pages",
            headers={
                "Authorization": f"Bearer {token}",
                "Notion-Version": NOTION_VERSION,
            },
            json=payload,
        )
    if response.status_code != 200:
        raise ValueError("Notion page creation failed")
    data = response.json()
    return {"id": data.get("id"), "url": data.get("url"), "title": title}


async def apify_run_actor(user_id: str, actor_id: str, actor_input: dict[str, Any] | None = None) -> dict[str, Any]:
    token = await _require_secret(user_id, "apify")
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{APIFY_API}/acts/{actor_id}/runs",
            params={"token": token},
            json=actor_input or {},
        )
    if response.status_code not in {200, 201}:
        raise ValueError("Apify actor run failed")
    data = response.json().get("data", {})
    return {
        "run_id": data.get("id"),
        "status": data.get("status"),
        "default_dataset_id": data.get("defaultDatasetId"),
        "started_at": data.get("startedAt"),
    }


async def retell_get_concurrency(user_id: str) -> dict[str, Any]:
    token = await _require_secret(user_id, "retell")
    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.get(
            f"{RETELL_API}/get-concurrency",
            headers={"Authorization": f"Bearer {token}"},
        )
    if response.status_code != 200:
        raise ValueError("Retell authentication failed")
    data = response.json()
    return {
        "current_concurrency": data.get("current_concurrency"),
        "concurrency_limit": data.get("concurrency_limit"),
        "base_concurrency": data.get("base_concurrency"),
    }


async def retell_create_voice_agent(
    user_id: str,
    response_engine: dict[str, Any],
    voice_id: str,
    agent_name: str | None = None,
    language: str = "en-US",
    version_description: str | None = None,
    webhook_url: str | None = None,
    begin_message_delay_ms: int | None = None,
) -> dict[str, Any]:
    token = await _require_secret(user_id, "retell")
    payload: dict[str, Any] = {
        "response_engine": response_engine,
        "voice_id": voice_id,
        "language": language,
    }
    if agent_name:
        payload["agent_name"] = agent_name
    if version_description:
        payload["version_description"] = version_description
    if webhook_url:
        payload["webhook_url"] = webhook_url
    if begin_message_delay_ms is not None:
        payload["begin_message_delay_ms"] = begin_message_delay_ms

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{RETELL_API}/create-agent",
            headers={"Authorization": f"Bearer {token}"},
            json=payload,
        )
    if response.status_code not in {200, 201}:
        raise ValueError(f"Retell agent creation failed: {response.text}")
    data = response.json()
    return {
        "id": data.get("agent_id"),
        "title": data.get("agent_name") or agent_name or "Retell Voice Agent",
        "voice_id": data.get("voice_id"),
        "version": data.get("version"),
        "language": data.get("language") or language,
        "is_published": data.get("is_published"),
        "response_engine": data.get("response_engine"),
    }
