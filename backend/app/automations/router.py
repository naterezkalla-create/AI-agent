from fastapi import APIRouter, HTTPException
from datetime import datetime, timezone
from app.entities.models import AutomationCreate, AutomationUpdate
from app.memory.supabase_client import get_supabase
from app.automations.scheduler import add_automation_job, remove_automation_job

router = APIRouter(prefix="/automations", tags=["automations"])


@router.post("/")
async def create_automation(body: AutomationCreate):
    sb = get_supabase()
    now = datetime.now(timezone.utc).isoformat()
    result = sb.table("automations").insert({
        "user_id": body.user_id,
        "name": body.name,
        "cron_expression": body.cron_expression,
        "prompt": body.prompt,
        "enabled": body.enabled,
        "created_at": now,
    }).execute()

    auto = result.data[0]

    if body.enabled:
        await add_automation_job(auto["id"], body.user_id, body.name, body.cron_expression, body.prompt)

    return auto


@router.get("/")
async def list_automations(user_id: str = "default"):
    sb = get_supabase()
    result = sb.table("automations").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
    return result.data


@router.patch("/{automation_id}")
async def update_automation(automation_id: str, body: AutomationUpdate):
    sb = get_supabase()
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    result = sb.table("automations").update(updates).eq("id", automation_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Automation not found")

    auto = result.data[0]
    auto_user_id = body.user_id or auto.get("user_id", "default")

    # Re-schedule or remove based on enabled state
    if auto.get("enabled"):
        await add_automation_job(auto["id"], auto_user_id, auto["name"], auto["cron_expression"], auto["prompt"])
    else:
        remove_automation_job(auto["id"])

    return auto


@router.delete("/{automation_id}")
async def delete_automation(automation_id: str):
    sb = get_supabase()
    remove_automation_job(automation_id)
    result = sb.table("automations").delete().eq("id", automation_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Automation not found")
    return {"deleted": True}
