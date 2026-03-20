import logging
from datetime import datetime, timezone
from typing import Optional, List, Union
from app.memory.supabase_client import get_supabase

logger = logging.getLogger(__name__)

MAX_MESSAGES = 50  # Keep last N messages to stay within context window


async def get_or_create_conversation(user_id: str, conversation_id: Optional[str] = None) -> dict:
    """Get existing conversation or create a new one."""
    sb = get_supabase()

    if conversation_id:
        result = sb.table("conversations").select("*").eq("id", conversation_id).eq("user_id", user_id).execute()
        if result.data:
            return result.data[0]

    # Create new conversation
    new_conv = {
        "user_id": user_id,
        "title": "New conversation",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    result = sb.table("conversations").insert(new_conv).execute()
    return result.data[0]


async def get_conversation(user_id: str, conversation_id: str) -> Optional[dict]:
    """Fetch a conversation only if it belongs to the given user."""
    sb = get_supabase()
    result = sb.table("conversations").select("*").eq("id", conversation_id).eq("user_id", user_id).execute()
    return result.data[0] if result.data else None


async def load_messages(conversation_id: str) -> List[dict]:
    """Load message history for a conversation."""
    sb = get_supabase()
    result = (
        sb.table("messages")
        .select("*")
        .eq("conversation_id", conversation_id)
        .order("created_at", desc=False)
        .limit(MAX_MESSAGES)
        .execute()
    )

    messages = []
    for row in result.data:
        msg: dict = {"role": row["role"]}

        # Handle tool_calls stored as JSON
        if row.get("tool_calls"):
            msg["content"] = row["tool_calls"]
        else:
            msg["content"] = row["content"] or ""

        messages.append(msg)

    return messages


async def save_message(
    conversation_id: str,
    role: str,
    content: Optional[Union[str, List]] = None,
    tool_calls: Optional[List] = None,
) -> dict:
    """Save a message to the conversation."""
    sb = get_supabase()

    row = {
        "conversation_id": conversation_id,
        "role": role,
        "content": content if isinstance(content, str) else None,
        "tool_calls": tool_calls or (content if isinstance(content, list) else None),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    result = sb.table("messages").insert(row).execute()

    # Update conversation timestamp
    sb.table("conversations").update(
        {"updated_at": datetime.now(timezone.utc).isoformat()}
    ).eq("id", conversation_id).execute()

    return result.data[0]


async def update_conversation_title(conversation_id: str, title: str) -> None:
    sb = get_supabase()
    sb.table("conversations").update({"title": title}).eq("id", conversation_id).execute()


async def list_conversations(user_id: str, limit: int = 50) -> List[dict]:
    sb = get_supabase()
    result = (
        sb.table("conversations")
        .select("*")
        .eq("user_id", user_id)
        .order("updated_at", desc=True)
        .limit(limit)
        .execute()
    )
    return result.data


async def delete_conversation(conversation_id: str, user_id: str) -> None:
    sb = get_supabase()
    convo = sb.table("conversations").select("id").eq("id", conversation_id).eq("user_id", user_id).execute()
    if not convo.data:
        return
    sb.table("messages").delete().eq("conversation_id", conversation_id).execute()
    sb.table("conversations").delete().eq("id", conversation_id).eq("user_id", user_id).execute()
