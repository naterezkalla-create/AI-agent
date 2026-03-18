"""
Core Agent Loop

The brain of the system. Orchestrates:
1. Receive user message
2. Load conversation history
3. Build system prompt (templates + memory)
4. Call Claude with messages + tools
5. If Claude returns tool_use → execute → feed result back → loop
6. If Claude returns text → return to user
7. Save all messages to conversation history
"""

import logging
from typing import AsyncIterator, Optional, List
from dataclasses import dataclass, field

from app.core import llm
from app.core.system_prompt import build_system_prompt
from app.core.conversation import (
    get_or_create_conversation,
    load_messages,
    save_message,
)
from app.tools.registry import get_claude_tools_schema
from app.tools.executor import execute_tool

logger = logging.getLogger(__name__)

MAX_TOOL_ITERATIONS = 15  # Safety limit to prevent infinite tool loops


@dataclass
class AgentResponse:
    """Result of running the agent loop."""
    text: str
    conversation_id: str
    tool_calls: List[dict] = field(default_factory=list)


async def run(
    user_message: str,
    user_id: str = "default",
    conversation_id: Optional[str] = None,
) -> AgentResponse:
    """
    Run the full agent loop for a single user message.

    Returns the agent's final text response along with any tool calls made.
    """
    # 1. Get or create conversation
    conversation = await get_or_create_conversation(user_id, conversation_id)
    conv_id = conversation["id"]

    # 2. Build system prompt
    system_prompt = await build_system_prompt(user_id)

    # 3. Load conversation history
    messages = await load_messages(conv_id)

    # 4. Append user message
    messages.append({"role": "user", "content": user_message})
    await save_message(conv_id, "user", content=user_message)

    # 5. Get tools
    tools = get_claude_tools_schema()

    # 6. Agent loop — keep calling Claude until we get a text response
    all_tool_calls = []

    for iteration in range(MAX_TOOL_ITERATIONS):
        logger.info(f"Agent loop iteration {iteration + 1}, messages: {len(messages)}")

        response = await llm.chat(
            messages=messages,
            system=system_prompt,
            tools=tools if tools else None,
            user_id=user_id,
        )

        # Check stop reason
        if response.stop_reason == "tool_use":
            # Extract all content blocks (text + tool_use)
            assistant_content = []
            tool_uses = []

            for block in response.content:
                if block.type == "text":
                    assistant_content.append({
                        "type": "text",
                        "text": block.text,
                    })
                elif block.type == "tool_use":
                    assistant_content.append({
                        "type": "tool_use",
                        "id": block.id,
                        "name": block.name,
                        "input": block.input,
                    })
                    tool_uses.append(block)

            # Add assistant message with tool calls
            messages.append({"role": "assistant", "content": assistant_content})

            # Execute each tool and collect results
            tool_results = []
            for tool_use in tool_uses:
                logger.info(f"Calling tool: {tool_use.name}")
                result = await execute_tool(tool_use.name, tool_use.input)

                # Extract result or error, and ensure it's a string
                tool_result_content = result.get("result", result.get("error", "No result"))
                if not isinstance(tool_result_content, str):
                    import json
                    tool_result_content = json.dumps(tool_result_content, default=str)

                # Content must be a string or list of content blocks
                tool_result = {
                    "type": "tool_result",
                    "tool_use_id": tool_use.id,
                    "content": tool_result_content,
                }
                
                tool_results.append(tool_result)
                logger.info(f"Tool result for {tool_use.name}: {tool_result_content[:200] if len(str(tool_result_content)) > 200 else tool_result_content}")

                all_tool_calls.append({
                    "name": tool_use.name,
                    "input": tool_use.input,
                    "result": tool_result_content[:1000],  # Truncate for storage
                })

            # Add tool results message
            messages.append({"role": "user", "content": tool_results})

        else:
            # End turn or max tokens — extract final text
            final_text = ""
            for block in response.content:
                if block.type == "text":
                    final_text += block.text

            # Save assistant response
            await save_message(conv_id, "assistant", content=final_text)

            # Also save any tool calls made during this turn
            if all_tool_calls:
                # Save tool interactions as part of conversation
                for tc in all_tool_calls:
                    await save_message(
                        conv_id, "assistant",
                        content=f"[Tool: {tc['name']}] Input: {str(tc['input'])[:500]}",
                        tool_calls=[tc],
                    )

            return AgentResponse(
                text=final_text,
                conversation_id=conv_id,
                tool_calls=all_tool_calls,
            )

    # Safety: if we hit max iterations, return what we have
    logger.warning(f"Agent hit max tool iterations ({MAX_TOOL_ITERATIONS})")
    return AgentResponse(
        text="I've reached my tool call limit for this turn. Here's what I've done so far. Please let me know if you need me to continue.",
        conversation_id=conv_id,
        tool_calls=all_tool_calls,
    )


async def run_stream(
    user_message: str,
    user_id: str = "default",
    conversation_id: Optional[str] = None,
) -> AsyncIterator[dict]:
    """
    Streaming version of the agent loop.
    Yields events: {"type": "text_delta", "text": "..."} or {"type": "tool_call", ...} or {"type": "done", ...}

    Note: Tool calls still block (can't stream tool results). Text responses stream token-by-token.
    """
    conversation = await get_or_create_conversation(user_id, conversation_id)
    conv_id = conversation["id"]
    system_prompt = await build_system_prompt(user_id)
    messages = await load_messages(conv_id)

    messages.append({"role": "user", "content": user_message})
    await save_message(conv_id, "user", content=user_message)

    tools = get_claude_tools_schema()
    all_tool_calls = []

    for iteration in range(MAX_TOOL_ITERATIONS):
        # For tool iterations, use non-streaming to simplify
        response = await llm.chat(
            messages=messages,
            system=system_prompt,
            tools=tools if tools else None,
            user_id=user_id,
        )

        if response.stop_reason == "tool_use":
            assistant_content = []
            tool_uses = []

            for block in response.content:
                if block.type == "text":
                    assistant_content.append({"type": "text", "text": block.text})
                    yield {"type": "text_delta", "text": block.text}
                elif block.type == "tool_use":
                    assistant_content.append({
                        "type": "tool_use",
                        "id": block.id,
                        "name": block.name,
                        "input": block.input,
                    })
                    tool_uses.append(block)

            messages.append({"role": "assistant", "content": assistant_content})

            tool_results = []
            for tool_use in tool_uses:
                yield {"type": "tool_call_start", "name": tool_use.name, "input": tool_use.input}
                result = await execute_tool(tool_use.name, tool_use.input)
                
                # Extract result and ensure it's a string
                tool_result_content = result.get("result", result.get("error", "No result"))
                if not isinstance(tool_result_content, str):
                    import json
                    tool_result_content = json.dumps(tool_result_content, default=str)

                tool_result = {
                    "type": "tool_result",
                    "tool_use_id": tool_use.id,
                    "content": tool_result_content,
                }
                
                tool_results.append(tool_result)
                all_tool_calls.append({
                    "name": tool_use.name,
                    "input": tool_use.input,
                    "result": tool_result_content[:1000],
                })
                yield {"type": "tool_call_end", "name": tool_use.name, "result": tool_result_content[:500]}

            messages.append({"role": "user", "content": tool_results})

        else:
            # Final text response
            final_text = ""
            for block in response.content:
                if block.type == "text":
                    final_text += block.text
                    yield {"type": "text_delta", "text": block.text}

            await save_message(conv_id, "assistant", content=final_text)
            yield {"type": "done", "conversation_id": conv_id, "tool_calls": all_tool_calls}
            return

    yield {"type": "done", "conversation_id": conv_id, "tool_calls": all_tool_calls, "truncated": True}
