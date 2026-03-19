from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from app.memory.long_term import get_memory_notes
from app.config import get_settings
from app.memory.supabase_client import get_supabase
import logging

logger = logging.getLogger(__name__)

PROMPTS_DIR = Path(__file__).parent.parent.parent / "prompts"


def _read_template(filename: str) -> str:
    """Read a prompt template file, return empty string if missing."""
    path = PROMPTS_DIR / filename
    if path.exists():
        return path.read_text().strip()
    logger.warning(f"Prompt template not found: {path}")
    return ""


async def get_user_custom_prompt(user_id: str = "default") -> str:
    """Fetch custom system prompt from user settings, if it exists."""
    try:
        sb = get_supabase()
        result = sb.table("user_settings").select("system_prompt").eq("user_id", user_id).execute()
        if result.data and result.data[0].get("system_prompt"):
            return result.data[0]["system_prompt"]
    except Exception as e:
        logger.warning(f"Failed to fetch custom system prompt for {user_id}: {e}")
    return ""


async def build_system_prompt(user_id: str = "default") -> str:
    """
    Assemble the full system prompt from templates + memory + custom settings.

    Structure:
    1. Custom system prompt (if set in settings)
    2. OR Identity + Instructions (template-based)
    3. User context
    4. Memory (injected long-term notes)
    5. Tool guidance
    """
    # Try to fetch custom system prompt from settings
    custom_prompt = await get_user_custom_prompt(user_id)
    
    if custom_prompt:
        # Use custom prompt as base, but still add memory and context
        base_prompt = custom_prompt
    else:
        # Fall back to template-based system prompt
        identity = _read_template("identity.md")
        instructions = _read_template("instructions.md")
        base_prompt = "\n\n".join(section for section in [identity, instructions] if section)

    # Load long-term memory notes
    memory_notes = await get_memory_notes(user_id)
    memory_section = ""
    if memory_notes:
        memory_lines = []
        for note in memory_notes:
            category = note.get("category", "general")
            key = note.get("key", "")
            content = note.get("content", "")
            memory_lines.append(f"- [{category}] {key}: {content}")
        memory_section = "## Your Memory\nThese are facts you've previously saved:\n" + "\n".join(memory_lines)

    # Load user context from templates
    user_context = _read_template("user.md")

    melbourne_now = datetime.now(ZoneInfo("Australia/Melbourne"))
    current_context = "\n".join(
        [
            "## Current Date/Time",
            f"- Current date in Melbourne: {melbourne_now.strftime('%Y-%m-%d')}",
            f"- Current time in Melbourne: {melbourne_now.strftime('%H:%M:%S %Z')}",
            f"- Current month in Melbourne: {melbourne_now.strftime('%B %Y')}",
            "- When the user refers to relative dates like today, tomorrow, next week, or this month, resolve them from this Melbourne date.",
        ]
    )

    sections = [
        base_prompt,
        current_context,
        user_context,
        memory_section,
    ]

    return "\n\n".join(section for section in sections if section)
