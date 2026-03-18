import os
from pathlib import Path
from app.tools.base import BaseTool
from app.config import get_settings


def _safe_path(filepath: str) -> Path:
    """Ensure path is within sandbox directory."""
    settings = get_settings()
    sandbox = Path(settings.sandbox_dir).resolve()
    sandbox.mkdir(parents=True, exist_ok=True)
    target = (sandbox / filepath).resolve()
    if not str(target).startswith(str(sandbox)):
        raise ValueError(f"Path traversal detected: {filepath}")
    return target


class ReadFileTool(BaseTool):
    @property
    def name(self) -> str:
        return "read_file"

    @property
    def description(self) -> str:
        return "Read the contents of a file in the workspace/sandbox."

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Relative path to the file within the sandbox"},
            },
            "required": ["path"],
        }

    async def execute(self, path: str) -> str:
        target = _safe_path(path)
        if not target.exists():
            return f"File not found: {path}"
        content = target.read_text()
        if len(content) > 50000:
            return content[:50000] + "\n\n... [truncated, file too large]"
        return content


class WriteFileTool(BaseTool):
    @property
    def name(self) -> str:
        return "write_file"

    @property
    def description(self) -> str:
        return "Write content to a file in the workspace/sandbox. Creates directories as needed."

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Relative path to the file within the sandbox"},
                "content": {"type": "string", "description": "Content to write to the file"},
            },
            "required": ["path", "content"],
        }

    async def execute(self, path: str, content: str) -> str:
        target = _safe_path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content)
        return f"File written: {path} ({len(content)} bytes)"


class ListFilesTool(BaseTool):
    @property
    def name(self) -> str:
        return "list_files"

    @property
    def description(self) -> str:
        return "List files and directories in a path within the workspace/sandbox."

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Relative directory path within the sandbox (default: root)",
                    "default": ".",
                },
            },
        }

    async def execute(self, path: str = ".") -> str:
        target = _safe_path(path)
        if not target.exists():
            return f"Directory not found: {path}"
        if not target.is_dir():
            return f"Not a directory: {path}"

        entries = []
        for item in sorted(target.iterdir()):
            prefix = "📁 " if item.is_dir() else "📄 "
            rel = item.relative_to(_safe_path("."))
            entries.append(f"{prefix}{rel}")

        return "\n".join(entries) if entries else "Directory is empty."
