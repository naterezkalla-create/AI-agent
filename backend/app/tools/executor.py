import json
import logging
import traceback
import inspect
from typing import Any, Dict
from app.tools import registry

logger = logging.getLogger(__name__)


async def execute_tool(name: str, input_data: dict, *, user_id: str = "default") -> Dict[str, Any]:
    """
    Execute a tool by name with given input.
    Returns a dict with 'result' or 'error' key.
    """
    tool = registry.get_tool(name)

    if tool is None:
        logger.error(f"Tool not found: {name}")
        return {"error": f"Tool '{name}' not found."}

    try:
        logger.info(f"Executing tool: {name} with input: {json.dumps(input_data)[:500]}")
        execute_kwargs = dict(input_data)
        if "user_id" in inspect.signature(tool.execute).parameters:
            execute_kwargs["user_id"] = user_id
        result = await tool.execute(**execute_kwargs)

        # Ensure result is serializable
        if isinstance(result, (dict, list)):
            result_str = json.dumps(result, indent=2, default=str)
        else:
            result_str = str(result)

        logger.info(f"Tool {name} completed. Result length: {len(result_str)}")
        return {"result": result_str}

    except Exception as e:
        error_msg = f"Tool '{name}' failed: {type(e).__name__}: {e}"
        logger.error(f"{error_msg}\n{traceback.format_exc()}")
        return {"error": error_msg}
