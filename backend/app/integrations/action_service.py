"""External action request lifecycle and managed resource tracking."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException

from app.events.bus import event_bus
from app.integrations.action_registry import ACTION_REGISTRY, list_external_actions
from app.memory.supabase_client import get_supabase


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _get_action_definition(action_name: str) -> dict[str, Any]:
    definition = ACTION_REGISTRY.get(action_name)
    if not definition:
        raise HTTPException(status_code=400, detail=f"Unsupported external action: {action_name}")
    return definition


def _normalize_resource_name(resource_type: str, result: dict[str, Any], payload: dict[str, Any]) -> str:
    return (
        result.get("title")
        or result.get("name")
        or payload.get("title")
        or payload.get("name")
        or payload.get("actor_id")
        or resource_type
    )


async def list_action_catalog() -> list[dict[str, Any]]:
    return list_external_actions()


async def list_external_resources(user_id: str, provider: str | None = None) -> list[dict[str, Any]]:
    sb = get_supabase()
    query = sb.table("external_resources").select("*").eq("user_id", user_id)
    if provider:
        query = query.eq("provider", provider)
    result = query.order("updated_at", desc=True).execute()
    return result.data


async def list_action_requests(user_id: str, status: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
    sb = get_supabase()
    query = sb.table("external_action_requests").select("*").eq("user_id", user_id)
    if status:
        query = query.eq("status", status)
    result = query.order("updated_at", desc=True).limit(limit).execute()
    return result.data


async def create_action_request(
    *,
    user_id: str,
    provider: str,
    action_name: str,
    payload: dict[str, Any],
    requested_by: str = "user",
    auto_execute: bool = False,
) -> dict[str, Any]:
    definition = _get_action_definition(action_name)
    if definition["provider"] != provider:
        raise HTTPException(status_code=400, detail="Provider does not match action")

    now = _now_iso()
    record = {
        "user_id": user_id,
        "provider": provider,
        "action_name": action_name,
        "resource_type": definition["resource_type"],
        "status": "proposed",
        "risk_level": definition["risk_level"],
        "requires_approval": definition["requires_approval"],
        "payload": payload,
        "requested_by": requested_by,
        "created_at": now,
        "updated_at": now,
    }
    sb = get_supabase()
    created = sb.table("external_action_requests").insert(record).execute().data[0]
    await event_bus.publish(
        "external_actions.changed",
        {"action": "created", "request": created},
        user_id=user_id,
        topics={"external_actions", "integrations"},
    )

    if auto_execute and not definition["requires_approval"]:
        return await approve_action_request(created["id"], user_id, approver="system")
    return created


async def _upsert_external_resource(
    *,
    user_id: str,
    provider: str,
    resource_type: str,
    remote_id: str,
    name: str,
    config: dict[str, Any],
    status: str,
    last_error: str | None = None,
) -> dict[str, Any]:
    sb = get_supabase()
    now = _now_iso()
    existing = (
        sb.table("external_resources")
        .select("*")
        .eq("user_id", user_id)
        .eq("provider", provider)
        .eq("resource_type", resource_type)
        .eq("remote_id", remote_id)
        .limit(1)
        .execute()
    )
    payload = {
        "name": name,
        "config": config,
        "status": status,
        "last_synced_at": now,
        "last_error": last_error,
        "updated_at": now,
    }
    if existing.data:
        result = sb.table("external_resources").update(payload).eq("id", existing.data[0]["id"]).execute()
        resource = result.data[0]
    else:
        resource = sb.table("external_resources").insert(
            {
                "user_id": user_id,
                "provider": provider,
                "resource_type": resource_type,
                "remote_id": remote_id,
                "name": name,
                "config": config,
                "status": status,
                "last_synced_at": now,
                "last_error": last_error,
                "created_at": now,
                "updated_at": now,
            }
        ).execute().data[0]
    await event_bus.publish(
        "external_resources.changed",
        {"action": "upserted", "resource": resource},
        user_id=user_id,
        topics={"external_resources", "integrations"},
    )
    return resource


async def approve_action_request(request_id: str, user_id: str, approver: str = "user") -> dict[str, Any]:
    sb = get_supabase()
    fetched = (
        sb.table("external_action_requests")
        .select("*")
        .eq("id", request_id)
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )
    if not fetched.data:
        raise HTTPException(status_code=404, detail="External action request not found")

    action_request = fetched.data[0]
    definition = _get_action_definition(action_request["action_name"])
    handler = definition["handler"]
    payload = action_request.get("payload") or {}
    now = _now_iso()

    try:
        result = await handler(user_id=user_id, **payload)
        result_payload = result if isinstance(result, dict) else {"result": result}
        resource_id = None
        if isinstance(result_payload, dict):
            remote_id = (
                result_payload.get("id")
                or result_payload.get("run_id")
                or result_payload.get("remote_id")
            )
            if remote_id:
                resource = await _upsert_external_resource(
                    user_id=user_id,
                    provider=action_request["provider"],
                    resource_type=action_request["resource_type"],
                    remote_id=str(remote_id),
                    name=_normalize_resource_name(action_request["resource_type"], result_payload, payload),
                    config=result_payload,
                    status="active",
                )
                resource_id = resource["id"]

        updated = (
            sb.table("external_action_requests")
            .update(
                {
                    "status": "executed",
                    "result": result_payload,
                    "approved_by": approver,
                    "approved_at": now,
                    "executed_at": now,
                    "external_resource_id": resource_id,
                    "updated_at": now,
                }
            )
            .eq("id", request_id)
            .execute()
            .data[0]
        )
        await event_bus.publish(
            "external_actions.changed",
            {"action": "executed", "request": updated},
            user_id=user_id,
            topics={"external_actions", "integrations", "external_resources"},
        )
        return updated
    except Exception as exc:
        updated = (
            sb.table("external_action_requests")
            .update(
                {
                    "status": "failed",
                    "result": {"error": str(exc)},
                    "approved_by": approver,
                    "approved_at": now,
                    "executed_at": now,
                    "updated_at": now,
                }
            )
            .eq("id", request_id)
            .execute()
            .data[0]
        )
        await event_bus.publish(
            "external_actions.changed",
            {"action": "failed", "request": updated},
            user_id=user_id,
            topics={"external_actions", "integrations"},
        )
        raise HTTPException(status_code=400, detail=str(exc)) from exc


async def reject_action_request(request_id: str, user_id: str) -> dict[str, Any]:
    sb = get_supabase()
    now = _now_iso()
    result = (
        sb.table("external_action_requests")
        .update({"status": "rejected", "updated_at": now})
        .eq("id", request_id)
        .eq("user_id", user_id)
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="External action request not found")
    request_row = result.data[0]
    await event_bus.publish(
        "external_actions.changed",
        {"action": "rejected", "request": request_row},
        user_id=user_id,
        topics={"external_actions", "integrations"},
    )
    return request_row
