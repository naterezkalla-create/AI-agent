"""Unified memory manager — single interface for short-term and long-term memory."""

from app.memory.short_term import (
    get_or_create_conversation,
    load_messages,
    save_message,
    list_conversations,
    delete_conversation,
)
from app.memory.long_term import (
    get_memory_notes,
    save_memory_note,
    delete_memory_note,
    search_memory_notes,
)

__all__ = [
    # Short-term
    "get_or_create_conversation",
    "load_messages",
    "save_message",
    "list_conversations",
    "delete_conversation",
    # Long-term
    "get_memory_notes",
    "save_memory_note",
    "delete_memory_note",
    "search_memory_notes",
]
