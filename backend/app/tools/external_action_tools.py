from __future__ import annotations

from app.tools.base import BaseTool
from app.integrations.action_service import (
    create_action_request,
    list_action_requests,
    list_external_resources,
)


class RequestRetellVoiceAgentTool(BaseTool):
    @property
    def name(self) -> str:
        return "request_retell_voice_agent"

    @property
    def description(self) -> str:
        return (
            "Create an approval-backed request to build a Retell AI voice agent. "
            "Use this when the user wants the system to create a new external voice agent in Retell."
        )

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "agent_name": {"type": "string", "description": "Name of the Retell voice agent"},
                "voice_id": {"type": "string", "description": "Retell voice ID to use"},
                "llm_id": {"type": "string", "description": "Retell LLM ID for the response engine"},
                "language": {"type": "string", "description": "Language code, e.g. en-US", "default": "en-US"},
                "version_description": {"type": "string", "description": "Optional version description"},
                "webhook_url": {"type": "string", "description": "Optional webhook URL for Retell callbacks"},
                "begin_message_delay_ms": {"type": "integer", "description": "Optional delay before the agent begins speaking"},
            },
            "required": ["agent_name", "voice_id", "llm_id"],
        }

    async def execute(
        self,
        agent_name: str,
        voice_id: str,
        llm_id: str,
        language: str = "en-US",
        version_description: str = "",
        webhook_url: str = "",
        begin_message_delay_ms: int | None = None,
        user_id: str = "default",
    ) -> str:
        payload = {
            "agent_name": agent_name,
            "voice_id": voice_id,
            "language": language,
            "response_engine": {
                "type": "retell-llm",
                "llm_id": llm_id,
                "version": 0,
            },
        }
        if version_description:
            payload["version_description"] = version_description
        if webhook_url:
            payload["webhook_url"] = webhook_url
        if begin_message_delay_ms is not None:
            payload["begin_message_delay_ms"] = begin_message_delay_ms

        request = await create_action_request(
            user_id=user_id,
            provider="retell",
            action_name="retell_create_voice_agent",
            payload=payload,
            requested_by="agent",
        )
        return (
            f"Created Retell voice agent request {request['id']} for '{agent_name}'. "
            "It is pending approval in the Integrations page."
        )


class ListExternalActionRequestsTool(BaseTool):
    @property
    def name(self) -> str:
        return "list_external_action_requests"

    @property
    def description(self) -> str:
        return "List pending or recent approval-backed external action requests."

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "description": "Optional status filter: proposed, executed, rejected, failed",
                },
            },
        }

    async def execute(self, status: str = "", user_id: str = "default") -> list:
        return await list_action_requests(user_id, status=status or None, limit=20)


class ListExternalResourcesTool(BaseTool):
    @property
    def name(self) -> str:
        return "list_external_resources"

    @property
    def description(self) -> str:
        return "List external resources the system has already created and is tracking."

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "provider": {
                    "type": "string",
                    "description": "Optional provider filter, e.g. retell or notion",
                },
            },
        }

    async def execute(self, provider: str = "", user_id: str = "default") -> list:
        return await list_external_resources(user_id, provider=provider or None)
