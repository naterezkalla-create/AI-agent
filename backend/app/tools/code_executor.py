import asyncio
import subprocess
import tempfile
from pathlib import Path
from app.tools.base import BaseTool
from app.config import get_settings


class CodeExecutorTool(BaseTool):
    @property
    def name(self) -> str:
        return "execute_code"

    @property
    def description(self) -> str:
        return "Execute Python code in a sandboxed environment. Use this to run calculations, data processing, or any Python code. The code runs in a subprocess with a 30-second timeout."

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "Python code to execute",
                },
                "language": {
                    "type": "string",
                    "description": "Programming language (currently only 'python' is supported)",
                    "default": "python",
                    "enum": ["python"],
                },
            },
            "required": ["code"],
        }

    async def execute(self, code: str, language: str = "python") -> str:
        settings = get_settings()
        sandbox = Path(settings.sandbox_dir)
        sandbox.mkdir(parents=True, exist_ok=True)

        # Write code to a temp file in the sandbox
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", dir=sandbox, delete=False
        ) as f:
            f.write(code)
            script_path = f.name

        try:
            result = await asyncio.to_thread(
                subprocess.run,
                ["python3", script_path],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=str(sandbox),
            )

            output = ""
            if result.stdout:
                output += result.stdout
            if result.stderr:
                output += ("\n--- STDERR ---\n" + result.stderr) if output else result.stderr

            if not output.strip():
                output = "(No output)"

            # Truncate if too long
            if len(output) > 10000:
                output = output[:10000] + "\n\n... [output truncated]"

            return output

        except subprocess.TimeoutExpired:
            return "Error: Code execution timed out (30 second limit)."
        finally:
            Path(script_path).unlink(missing_ok=True)
