import httpx
from app.tools.base import BaseTool
from app.config import get_settings


class WebSearchTool(BaseTool):
    @property
    def name(self) -> str:
        return "web_search"

    @property
    def description(self) -> str:
        return "Search the web for current information. Use this when you need up-to-date facts, news, or any information not in your training data."

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results to return (default: 5)",
                    "default": 5,
                },
            },
            "required": ["query"],
        }

    async def execute(self, query: str, max_results: int = 5) -> str:
        settings = get_settings()

        if not settings.tavily_api_key:
            return "Web search is not configured. Please set the TAVILY_API_KEY environment variable."

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": settings.tavily_api_key,
                    "query": query,
                    "max_results": max_results,
                    "include_answer": True,
                },
            )
            response.raise_for_status()
            data = response.json()

        results = []
        if data.get("answer"):
            results.append(f"**Summary:** {data['answer']}\n")

        for item in data.get("results", []):
            results.append(
                f"**{item['title']}**\n{item['url']}\n{item.get('content', '')[:300]}\n"
            )

        return "\n---\n".join(results) if results else "No results found."
