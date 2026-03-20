"""Admin endpoints — memory management, system info."""

from typing import Optional
from fastapi import APIRouter, Depends
from app.api.deps import get_current_user
from app.automations.scheduler import dispatch_platform_event
from app.entities.models import MemoryNoteCreate
from app.memory.long_term import (
    get_memory_notes,
    save_memory_note,
    delete_memory_note,
    search_memory_notes,
    update_memory_note,
)
from app.tools.registry import get_all_tools
from app.events.bus import event_bus

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/memory")
async def list_memory(category: Optional[str] = None, user_id: str = Depends(get_current_user)):
    """List all long-term memory notes."""
    return await get_memory_notes(user_id, category)


@router.post("/memory")
async def create_memory(body: MemoryNoteCreate, user_id: str = Depends(get_current_user)):
    """Create or update a memory note."""
    note = await save_memory_note(
        user_id,
        body.category,
        body.key,
        body.content,
        confidence=body.confidence,
        source=body.source,
        review_status=body.review_status,
    )
    await event_bus.publish(
        "memory.changed",
        {"action": "upserted", "key": body.key, "category": body.category},
        user_id=user_id,
        topics={"memory"},
    )
    await dispatch_platform_event(
        "memory.changed",
        user_id,
        {"action": "upserted", "key": body.key, "category": body.category},
    )
    return note


@router.patch("/memory/{key}")
async def patch_memory(key: str, body: dict, user_id: str = Depends(get_current_user)):
    """Update memory metadata or content."""
    updated = await update_memory_note(user_id, key, body)
    if updated:
        await event_bus.publish(
            "memory.changed",
            {"action": "updated", "key": key, "category": updated.get("category")},
            user_id=user_id,
            topics={"memory"},
        )
        await dispatch_platform_event(
            "memory.changed",
            user_id,
            {"action": "updated", "key": key, "category": updated.get("category")},
        )
    return updated or {"updated": False}


@router.delete("/memory/{key}")
async def remove_memory(key: str, user_id: str = Depends(get_current_user)):
    """Delete a memory note."""
    success = await delete_memory_note(user_id, key)
    if success:
        await event_bus.publish(
            "memory.changed",
            {"action": "deleted", "key": key},
            user_id=user_id,
            topics={"memory"},
        )
        await dispatch_platform_event("memory.changed", user_id, {"action": "deleted", "key": key})
    return {"deleted": success}


@router.get("/memory/search")
async def search_memory(query: str, user_id: str = Depends(get_current_user)):
    """Search memory notes by keyword."""
    return await search_memory_notes(user_id, query)


@router.get("/tools")
async def list_tools():
    """List all registered tools and their schemas."""
    tools = get_all_tools()
    return [
        {"name": t.name, "description": t.description, "parameters": t.parameters}
        for t in tools
    ]


@router.get("/status")
async def system_status():
    """Basic system health check."""
    tools = get_all_tools()
    return {
        "status": "ok",
        "tools_registered": len(tools),
        "tool_names": [t.name for t in tools],
    }
