"""Short-term memory: conversation history management.

All conversation CRUD is handled by core/conversation.py.
This module provides a thin convenience layer for the memory manager.
"""

from app.core.conversation import (
    get_or_create_conversation,
    load_messages,
    save_message,
    list_conversations,
    delete_conversation,
)

__all__ = [
    "get_or_create_conversation",
    "load_messages",
    "save_message",
    "list_conversations",
    "delete_conversation",
]
