from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timezone
from app.api.deps import get_current_user
from app.entities.models import AutomationCreate, AutomationUpdate
from app.memory.supabase_client import get_supabase
from app.automations.scheduler import (
    add_automation_job,
    remove_automation_job,
    list_automation_runs,
)
from app.events.bus import event_bus

router = APIRouter(prefix="/automations", tags=["automations"])


@router.post("/")
async def create_automation(body: AutomationCreate, user_id: str = Depends(get_current_user)):
    sb = get_supabase()
    now = datetime.now(timezone.utc).isoformat()
    result = sb.table("automations").insert({
        "user_id": user_id,
        "name": body.name,
        "cron_expression": body.cron_expression,
        "prompt": body.prompt,
        "enabled": body.enabled,
        "trigger_type": body.trigger_type,
        "trigger_config": body.trigger_config,
        "max_retries": body.max_retries,
        "retry_delay_seconds": body.retry_delay_seconds,
        "created_at": now,
    }).execute()

    auto = result.data[0]

    if body.enabled:
        await add_automation_job(
            auto["id"],
            user_id,
            body.name,
            body.cron_expression,
            body.prompt,
            trigger_type=body.trigger_type,
            trigger_config=body.trigger_config,
            enabled=body.enabled,
            max_retries=body.max_retries,
            retry_delay_seconds=body.retry_delay_seconds,
        )

    await event_bus.publish(
        "automations.changed",
        {"action": "created", "automation_id": auto["id"], "trigger_type": auto.get("trigger_type", "cron")},
        user_id=user_id,
        topics={"automations"},
    )

    return auto


@router.get("/")
async def list_automations(user_id: str = Depends(get_current_user)):
    sb = get_supabase()
    result = sb.table("automations").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
    return result.data


@router.get("/runs")
async def get_automation_runs(automation_id: str | None = None, limit: int = 50, user_id: str = Depends(get_current_user)):
    return await list_automation_runs(user_id=user_id, automation_id=automation_id, limit=limit)


@router.patch("/{automation_id}")
async def update_automation(automation_id: str, body: AutomationUpdate, user_id: str = Depends(get_current_user)):
    sb = get_supabase()
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    result = sb.table("automations").update(updates).eq("id", automation_id).eq("user_id", user_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Automation not found")

    auto = result.data[0]
    auto_user_id = auto.get("user_id", user_id)

    # Re-schedule or remove based on enabled state
    if auto.get("enabled"):
        await add_automation_job(
            auto["id"],
            auto_user_id,
            auto["name"],
            auto["cron_expression"],
            auto["prompt"],
            trigger_type=auto.get("trigger_type", "cron"),
            trigger_config=auto.get("trigger_config") or {},
            enabled=auto.get("enabled", True),
            max_retries=auto.get("max_retries", 2),
            retry_delay_seconds=auto.get("retry_delay_seconds", 60),
        )
    else:
        remove_automation_job(auto["id"])

    await event_bus.publish(
        "automations.changed",
        {"action": "updated", "automation_id": auto["id"], "trigger_type": auto.get("trigger_type", "cron")},
        user_id=auto_user_id,
        topics={"automations"},
    )
    return auto


@router.delete("/{automation_id}")
async def delete_automation(automation_id: str, user_id: str = Depends(get_current_user)):
    sb = get_supabase()
    remove_automation_job(automation_id)
    result = sb.table("automations").delete().eq("id", automation_id).eq("user_id", user_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Automation not found")
    deleted = result.data[0]
    await event_bus.publish(
        "automations.changed",
        {"action": "deleted", "automation_id": automation_id},
        user_id=deleted.get("user_id", "default"),
        topics={"automations"},
    )
    return {"deleted": True}
