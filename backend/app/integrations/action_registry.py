"""Registry for external provider actions that can create or mutate remote resources."""

from __future__ import annotations

from typing import Any, Awaitable, Callable

from app.integrations.external_services import (
    apify_run_actor,
    notion_create_page,
    retell_create_voice_agent,
)

ActionHandler = Callable[..., Awaitable[dict[str, Any] | list[dict[str, Any]] | str]]


ACTION_REGISTRY: dict[str, dict[str, Any]] = {
    "notion_create_page": {
        "provider": "notion",
        "resource_type": "notion_page",
        "description": "Create a page in Notion under a parent page.",
        "risk_level": "medium",
        "requires_approval": True,
        "handler": notion_create_page,
    },
    "apify_run_actor": {
        "provider": "apify",
        "resource_type": "apify_run",
        "description": "Run an Apify actor with structured input.",
        "risk_level": "medium",
        "requires_approval": True,
        "handler": apify_run_actor,
    },
    "retell_create_voice_agent": {
        "provider": "retell",
        "resource_type": "retell_voice_agent",
        "description": "Create a Retell AI voice agent using a configured response engine and voice.",
        "risk_level": "high",
        "requires_approval": True,
        "handler": retell_create_voice_agent,
    },
}


def list_external_actions() -> list[dict[str, Any]]:
    return [
        {
            "id": action_id,
            "provider": definition["provider"],
            "resource_type": definition["resource_type"],
            "description": definition["description"],
            "risk_level": definition["risk_level"],
            "requires_approval": definition["requires_approval"],
        }
        for action_id, definition in ACTION_REGISTRY.items()
    ]
