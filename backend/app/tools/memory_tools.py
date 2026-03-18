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
            },
            "required": ["category", "key", "content"],
        }

    async def execute(self, category: str, key: str, content: str) -> str:
        await save_memory_note("default", category, key, content)
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

    async def execute(self, query: str) -> str:
        results = await search_memory_notes("default", query)
        if not results:
            return "No matching memories found."

        lines = []
        for note in results:
            lines.append(f"[{note['category']}] {note['key']}: {note['content']}")
        return "\n".join(lines)
