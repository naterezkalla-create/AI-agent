"""CRUD operations for entities using Supabase."""

from datetime import datetime, timezone
from typing import Optional, List
from app.memory.supabase_client import get_supabase


async def create_entity(user_id: str, entity_type: str, data: dict) -> dict:
    sb = get_supabase()
    now = datetime.now(timezone.utc).isoformat()
    result = sb.table("entities").insert({
        "user_id": user_id,
        "type": entity_type,
        "data": data,
        "created_at": now,
        "updated_at": now,
    }).execute()
    return result.data[0]


async def get_entity(entity_id: str, user_id: str) -> Optional[dict]:
    sb = get_supabase()
    result = sb.table("entities").select("*").eq("id", entity_id).eq("user_id", user_id).execute()
    return result.data[0] if result.data else None


async def list_entities(user_id: str, entity_type: Optional[str] = None, limit: int = 50) -> List[dict]:
    sb = get_supabase()
    query = sb.table("entities").select("*").eq("user_id", user_id)
    if entity_type:
        query = query.eq("type", entity_type)
    result = query.order("created_at", desc=True).limit(limit).execute()
    return result.data


async def update_entity(entity_id: str, user_id: str, data: dict) -> Optional[dict]:
    sb = get_supabase()
    existing = await get_entity(entity_id, user_id)
    if not existing:
        return None

    merged = {**existing.get("data", {}), **data}
    now = datetime.now(timezone.utc).isoformat()
    result = sb.table("entities").update({
        "data": merged,
        "updated_at": now,
    }).eq("id", entity_id).eq("user_id", user_id).execute()
    return result.data[0] if result.data else None


async def delete_entity(entity_id: str, user_id: str) -> bool:
    sb = get_supabase()
    result = sb.table("entities").delete().eq("id", entity_id).eq("user_id", user_id).execute()
    return len(result.data) > 0
