"""Chat API endpoints."""

import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from app.api.deps import get_current_user
from app.entities.models import ChatRequest, ChatResponse
from app.core.agent import run, run_stream
from app.core.conversation import list_conversations, delete_conversation, load_messages, get_conversation
from app.events.bus import event_bus

router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat(body: ChatRequest, user_id: str = Depends(get_current_user)):
    """Send a message to the agent and get a response."""
    result = await run(
        user_message=body.message,
        user_id=user_id,
        conversation_id=body.conversation_id,
    )
    await event_bus.publish(
        "conversation.updated",
        {
            "conversation_id": result.conversation_id,
            "preview": result.text[:160],
            "tool_calls": len(result.tool_calls),
        },
        user_id=user_id,
        topics={"conversation", "chat"},
    )
    return ChatResponse(
        response=result.text,
        conversation_id=result.conversation_id,
        tool_calls=result.tool_calls,
    )


@router.post("/chat/stream")
async def chat_stream(body: ChatRequest, user_id: str = Depends(get_current_user)):
    """Stream chat events as server-sent events."""

    async def event_generator():
        final_event = None
        async for event in run_stream(
            user_message=body.message,
            user_id=user_id,
            conversation_id=body.conversation_id,
        ):
            if event.get("type") == "done":
                final_event = event
            yield f"data: {json.dumps(event)}\n\n"

        if final_event:
            await event_bus.publish(
                "conversation.updated",
                {
                    "conversation_id": final_event.get("conversation_id"),
                    "tool_calls": len(final_event.get("tool_calls", [])),
                },
                user_id=user_id,
                topics={"conversation", "chat"},
            )

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
async def get_conversations(user_id: str = Depends(get_current_user)):
    """List all conversations for a user."""
    return await list_conversations(user_id)


@router.get("/conversations/{conversation_id}/messages")
async def get_conversation_messages(conversation_id: str, user_id: str = Depends(get_current_user)):
    """Load the full message history for a conversation."""
    conversation = await get_conversation(user_id, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return await load_messages(conversation_id)


@router.delete("/conversations/{conversation_id}")
async def remove_conversation(conversation_id: str, user_id: str = Depends(get_current_user)):
    """Delete a conversation and its messages."""
    await delete_conversation(conversation_id, user_id)
    await event_bus.publish(
        "conversation.deleted",
        {"conversation_id": conversation_id},
        user_id=user_id,
        topics={"conversation", "chat"},
    )
    return {"deleted": True}
