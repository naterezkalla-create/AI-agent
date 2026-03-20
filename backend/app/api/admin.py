"""Admin endpoints — memory management, system info."""

from typing import Optional
from fastapi import APIRouter
from app.entities.models import MemoryNoteCreate
from app.memory.long_term import (
    get_memory_notes,
    save_memory_note,
    delete_memory_note,
    search_memory_notes,
    update_memory_note,
)
from app.tools.registry import get_all_tools

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/memory")
async def list_memory(user_id: str = "default", category: Optional[str] = None):
    """List all long-term memory notes."""
    return await get_memory_notes(user_id, category)


@router.post("/memory")
async def create_memory(body: MemoryNoteCreate, user_id: str = "default"):
    """Create or update a memory note."""
    return await save_memory_note(
        user_id,
        body.category,
        body.key,
        body.content,
        confidence=body.confidence,
        source=body.source,
        review_status=body.review_status,
    )


@router.patch("/memory/{key}")
async def patch_memory(key: str, body: dict, user_id: str = "default"):
    """Update memory metadata or content."""
    updated = await update_memory_note(user_id, key, body)
    return updated or {"updated": False}


@router.delete("/memory/{key}")
async def remove_memory(key: str, user_id: str = "default"):
    """Delete a memory note."""
    success = await delete_memory_note(user_id, key)
    return {"deleted": success}


@router.get("/memory/search")
async def search_memory(query: str, user_id: str = "default"):
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
