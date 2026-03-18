from abc import ABC, abstractmethod
from typing import Any


class BaseTool(ABC):
    """Abstract base class for all agent tools."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique tool name (snake_case)."""
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """Description shown to the LLM."""
        ...

    @property
    @abstractmethod
    def parameters(self) -> dict:
        """JSON Schema for the tool's input parameters."""
        ...

    @abstractmethod
    async def execute(self, **kwargs) -> Any:
        """Execute the tool with the given parameters. Return a string or dict result."""
        ...

    def to_claude_schema(self) -> dict:
        """Convert to Anthropic tool format."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.parameters,
        }
