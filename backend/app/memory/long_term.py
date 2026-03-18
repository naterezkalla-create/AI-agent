"""Long-term memory: persistent notes/facts stored in Supabase."""

import logging
from datetime import datetime, timezone
from typing import Optional, List
from app.memory.supabase_client import get_supabase

logger = logging.getLogger(__name__)


async def get_memory_notes(user_id: str, category: Optional[str] = None) -> List[dict]:
    """Retrieve all long-term memory notes for a user."""
    sb = get_supabase()
    query = sb.table("memory_notes").select("*").eq("user_id", user_id)
    if category:
        query = query.eq("category", category)
    result = query.order("created_at", desc=False).execute()
    return result.data


async def save_memory_note(user_id: str, category: str, key: str, content: str) -> dict:
    """Save or update a memory note. Upserts by (user_id, key)."""
    sb = get_supabase()
    now = datetime.now(timezone.utc).isoformat()

    # Check if note with this key exists
    existing = (
        sb.table("memory_notes")
        .select("id")
        .eq("user_id", user_id)
        .eq("key", key)
        .execute()
    )

    if existing.data:
        result = (
            sb.table("memory_notes")
            .update({"category": category, "content": content, "updated_at": now})
            .eq("id", existing.data[0]["id"])
            .execute()
        )
    else:
        result = sb.table("memory_notes").insert({
            "user_id": user_id,
            "category": category,
            "key": key,
            "content": content,
            "created_at": now,
            "updated_at": now,
        }).execute()

    return result.data[0]


async def delete_memory_note(user_id: str, key: str) -> bool:
    sb = get_supabase()
    result = (
        sb.table("memory_notes")
        .delete()
        .eq("user_id", user_id)
        .eq("key", key)
        .execute()
    )
    return len(result.data) > 0


async def search_memory_notes(user_id: str, query: str) -> List[dict]:
    """Simple keyword search across memory notes."""
    sb = get_supabase()
    # Use ilike for case-insensitive search across content and key
    result = (
        sb.table("memory_notes")
        .select("*")
        .eq("user_id", user_id)
        .or_(f"content.ilike.%{query}%,key.ilike.%{query}%")
        .execute()
    )
    return result.data
