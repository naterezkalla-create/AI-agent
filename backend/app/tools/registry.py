import logging
from typing import Optional, Dict, List
from app.tools.base import BaseTool

logger = logging.getLogger(__name__)

# Global tool registry
_tools: Dict[str, BaseTool] = {}


def register(tool: BaseTool) -> None:
    """Register a tool instance."""
    if tool.name in _tools:
        logger.warning(f"Tool '{tool.name}' already registered, overwriting.")
    _tools[tool.name] = tool
    logger.info(f"Registered tool: {tool.name}")


def get_tool(name: str) -> Optional[BaseTool]:
    return _tools.get(name)


def get_all_tools() -> List[BaseTool]:
    return list(_tools.values())


def get_claude_tools_schema() -> List[Dict]:
    """Return all tools in Anthropic's tool format."""
    return [tool.to_claude_schema() for tool in _tools.values()]


def register_all_tools() -> None:
    """Import and register all built-in tools."""
    from app.tools.web_search import WebSearchTool
    from app.tools.file_ops import ReadFileTool, WriteFileTool, ListFilesTool
    from app.tools.code_executor import CodeExecutorTool
    from app.tools.entity_tools import (
        CreateEntityTool,
        SearchEntitiesTool,
        UpdateEntityTool,
        DeleteEntityTool,
    )
    from app.tools.integration_tools import (
        SendEmailTool,
        ListInboxTool,
        CreateCalendarEventTool,
        ListCalendarEventsTool,
    )
    from app.tools.memory_tools import SaveMemoryTool, SearchMemoryTool

    tools = [
        WebSearchTool(),
        ReadFileTool(),
        WriteFileTool(),
        ListFilesTool(),
        CodeExecutorTool(),
        CreateEntityTool(),
        SearchEntitiesTool(),
        UpdateEntityTool(),
        DeleteEntityTool(),
        SendEmailTool(),
        ListInboxTool(),
        CreateCalendarEventTool(),
        ListCalendarEventsTool(),
        SaveMemoryTool(),
        SearchMemoryTool(),
    ]

    for tool in tools:
        register(tool)

    logger.info(f"Registered {len(tools)} tools total.")
