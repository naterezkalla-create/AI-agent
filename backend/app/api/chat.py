"""Chat API endpoints."""

from fastapi import APIRouter
from app.entities.models import ChatRequest, ChatResponse
from app.core.agent import run
from app.core.conversation import list_conversations, delete_conversation

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


@router.get("/conversations")
async def get_conversations(user_id: str = "default"):
    """List all conversations for a user."""
    return await list_conversations(user_id)


@router.delete("/conversations/{conversation_id}")
async def remove_conversation(conversation_id: str):
    """Delete a conversation and its messages."""
    await delete_conversation(conversation_id)
    return {"deleted": True}
