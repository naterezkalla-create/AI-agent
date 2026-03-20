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
    result = query.order("updated_at", desc=True).execute()
    return result.data


def _normalize_memory_text(value: str) -> str:
    return " ".join(value.lower().split())


async def save_memory_note(
    user_id: str,
    category: str,
    key: str,
    content: str,
    confidence: float = 0.8,
    source: str = "manual",
    review_status: str = "active",
) -> dict:
    """Save or update a memory note. Upserts by (user_id, key)."""
    sb = get_supabase()
    now = datetime.now(timezone.utc).isoformat()
    normalized_content = _normalize_memory_text(content)

    # Check if note with this key exists
    existing = (
        sb.table("memory_notes")
        .select("id, content, key")
        .eq("user_id", user_id)
        .execute()
    )

    duplicate = next(
        (
            note for note in existing.data
            if note["key"] == key or _normalize_memory_text(note.get("content", "")) == normalized_content
        ),
        None,
    )

    if duplicate:
        result = (
            sb.table("memory_notes")
            .update({
                "category": category,
                "key": key,
                "content": content,
                "confidence": confidence,
                "source": source,
                "review_status": review_status,
                "updated_at": now,
            })
            .eq("id", duplicate["id"])
            .execute()
        )
    else:
        result = sb.table("memory_notes").insert({
            "user_id": user_id,
            "category": category,
            "key": key,
            "content": content,
            "confidence": confidence,
            "source": source,
            "review_status": review_status,
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
        .order("updated_at", desc=True)
        .execute()
    )
    return result.data


async def update_memory_note(user_id: str, key: str, updates: dict) -> Optional[dict]:
    """Update memory metadata or content."""
    sb = get_supabase()
    payload = {**updates, "updated_at": datetime.now(timezone.utc).isoformat()}

    result = (
        sb.table("memory_notes")
        .update(payload)
        .eq("user_id", user_id)
        .eq("key", key)
        .execute()
    )
    return result.data[0] if result.data else None
