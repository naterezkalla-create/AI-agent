"""Registry describing supported integration providers."""

from __future__ import annotations

from typing import Any

from app.config import get_settings


PROVIDER_REGISTRY: dict[str, dict[str, Any]] = {
    "google": {
        "name": "Google Workspace",
        "category": "productivity",
        "description": "Calendar and Gmail connectivity for scheduling, summaries, and follow-ups.",
        "connection_mode": "oauth",
        "required_env": ["GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", "GOOGLE_REDIRECT_URI", "ENCRYPTION_KEY"],
        "user_secret_keys": [],
        "capabilities": ["calendar.read", "calendar.write", "gmail.read", "gmail.send"],
        "tools": ["create_calendar_event", "list_calendar_events"],
        "supports_realtime": True,
    },
    "slack": {
        "name": "Slack",
        "category": "communication",
        "description": "Workspace messaging, channel posting, and alert delivery.",
        "connection_mode": "api_key",
        "required_env": [],
        "user_secret_keys": ["slack"],
        "capabilities": ["channels.read", "chat.postMessage", "users.lookup"],
        "tools": ["slack_post_message"],
        "supports_realtime": True,
    },
    "github": {
        "name": "GitHub",
        "category": "developer",
        "description": "Repository metadata, issues, pull requests, and commit activity.",
        "connection_mode": "api_key",
        "required_env": [],
        "user_secret_keys": ["github"],
        "capabilities": ["repos.read", "issues.read", "pull_requests.read"],
        "tools": ["github_list_repos", "github_list_issues"],
        "supports_realtime": False,
    },
    "notion": {
        "name": "Notion",
        "category": "knowledge",
        "description": "Workspace pages, databases, and lightweight knowledge sync.",
        "connection_mode": "api_key",
        "required_env": [],
        "user_secret_keys": ["notion"],
        "capabilities": ["pages.read", "pages.write", "databases.read"],
        "tools": ["notion_search", "notion_create_page"],
        "supports_realtime": False,
    },
    "telegram": {
        "name": "Telegram",
        "category": "channel",
        "description": "Two-way messaging channel for the agent.",
        "connection_mode": "managed",
        "required_env": ["TELEGRAM_BOT_TOKEN"],
        "user_secret_keys": [],
        "capabilities": ["messages.receive", "messages.send"],
        "tools": [],
        "supports_realtime": True,
    },
    "apify": {
        "name": "Apify",
        "category": "data",
        "description": "Web data extraction and actor execution.",
        "connection_mode": "api_key",
        "required_env": [],
        "user_secret_keys": ["apify"],
        "capabilities": ["actors.run", "datasets.read"],
        "tools": ["apify_run_actor"],
        "supports_realtime": False,
    },
    "retell": {
        "name": "Retell AI",
        "category": "voice",
        "description": "Voice agents, calls, and conversational phone workflows.",
        "connection_mode": "api_key",
        "required_env": [],
        "user_secret_keys": ["retell"],
        "capabilities": ["voice_agents.create", "voice_agents.read", "calls.create"],
        "tools": ["request_retell_voice_agent", "retell_create_voice_agent"],
        "supports_realtime": False,
    },
    "custom_webhook": {
        "name": "Custom Webhook",
        "category": "automation",
        "description": "Receive events from any external app through a generated webhook endpoint.",
        "connection_mode": "webhook",
        "required_env": [],
        "user_secret_keys": [],
        "capabilities": ["events.receive", "triggers.webhook"],
        "tools": [],
        "supports_realtime": True,
    },
    "openai": {
        "name": "OpenAI",
        "category": "ai",
        "description": "Alternate model provider for future tool/model routing.",
        "connection_mode": "api_key",
        "required_env": [],
        "user_secret_keys": ["openai"],
        "capabilities": ["chat.completions"],
        "tools": [],
        "supports_realtime": False,
    },
    "anthropic": {
        "name": "Anthropic",
        "category": "ai",
        "description": "Primary model provider used for agent responses.",
        "connection_mode": "env_or_api_key",
        "required_env": ["ANTHROPIC_API_KEY"],
        "user_secret_keys": ["anthropic"],
        "capabilities": ["messages.create", "messages.stream"],
        "tools": [],
        "supports_realtime": True,
    },
}


def list_provider_definitions() -> list[dict[str, Any]]:
    """Return provider definitions annotated with environment readiness."""
    settings = get_settings()
    providers: list[dict[str, Any]] = []

    for provider_id, definition in PROVIDER_REGISTRY.items():
        required_env = definition.get("required_env", [])
        configured_env = [key for key in required_env if bool(getattr(settings, key.lower(), None))]

        providers.append(
            {
                "id": provider_id,
                **definition,
                "configured_env": configured_env,
                "is_env_ready": len(configured_env) == len(required_env),
            }
        )

    return providers
