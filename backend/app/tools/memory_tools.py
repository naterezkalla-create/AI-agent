from app.tools.base import BaseTool
from app.memory.long_term import save_memory_note, search_memory_notes


class SaveMemoryTool(BaseTool):
    @property
    def name(self) -> str:
        return "save_memory"

    @property
    def description(self) -> str:
        return "Save a fact, preference, or important information to long-term memory. Use this proactively when the user shares something worth remembering (names, preferences, business context, etc.)."

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "description": "Category for the memory (e.g., 'personal', 'business', 'preferences', 'contacts')",
                },
                "key": {
                    "type": "string",
                    "description": "A short unique identifier/title for this memory",
                },
                "content": {
                    "type": "string",
                    "description": "The information to remember",
                },
                "confidence": {
                    "type": "number",
                    "description": "Confidence score from 0 to 1 for how reliable this memory is",
                    "default": 0.8,
                },
            },
            "required": ["category", "key", "content"],
        }

    async def execute(self, category: str, key: str, content: str, confidence: float = 0.8, user_id: str = "default") -> str:
        await save_memory_note(user_id, category, key, content, confidence=confidence, source="agent")
        return f"Saved to memory [{category}] {key}: {content}"


class SearchMemoryTool(BaseTool):
    @property
    def name(self) -> str:
        return "search_memory"

    @property
    def description(self) -> str:
        return "Search your long-term memory for previously saved facts and information."

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search term to find in memory",
                },
            },
            "required": ["query"],
        }

    async def execute(self, query: str, user_id: str = "default") -> str:
        results = await search_memory_notes(user_id, query)
        if not results:
            return "No matching memories found."

        lines = []
        for note in results:
            lines.append(
                f"[{note['category']}] {note['key']} (confidence {note.get('confidence', 0.8):.1f}, status {note.get('review_status', 'active')}): {note['content']}"
            )
        return "\n".join(lines)
