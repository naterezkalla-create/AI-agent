"""Chat API endpoints."""

import json
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from app.entities.models import ChatRequest, ChatResponse
from app.core.agent import run, run_stream
from app.core.conversation import list_conversations, delete_conversation, load_messages

router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat(body: ChatRequest):
    """Send a message to the agent and get a response."""
    result = await run(
        user_message=body.message,
        user_id=body.user_id,
        conversation_id=body.conversation_id,
    )
    return ChatResponse(
        response=result.text,
        conversation_id=result.conversation_id,
        tool_calls=result.tool_calls,
    )


@router.post("/chat/stream")
async def chat_stream(body: ChatRequest):
    """Stream chat events as server-sent events."""

    async def event_generator():
        async for event in run_stream(
            user_message=body.message,
            user_id=body.user_id,
            conversation_id=body.conversation_id,
        ):
            yield f"data: {json.dumps(event)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/conversations")
async def get_conversations(user_id: str = "default"):
    """List all conversations for a user."""
    return await list_conversations(user_id)


@router.get("/conversations/{conversation_id}/messages")
async def get_conversation_messages(conversation_id: str):
    """Load the full message history for a conversation."""
    return await load_messages(conversation_id)


@router.delete("/conversations/{conversation_id}")
async def remove_conversation(conversation_id: str):
    """Delete a conversation and its messages."""
    await delete_conversation(conversation_id)
    return {"deleted": True}
