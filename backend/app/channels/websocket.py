"""WebSocket endpoint for real-time chat with the agent."""

import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.api.deps import get_current_user_ws
from app.core.agent import run_stream

logger = logging.getLogger(__name__)

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """WebSocket endpoint that streams agent responses."""
    await websocket.accept()
    logger.info("WebSocket client connected")

    conversation_id = None

    try:
        user_id = await get_current_user_ws(websocket)
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            payload = json.loads(data)

            user_message = payload.get("message", "")
            conversation_id = payload.get("conversation_id", conversation_id)

            if not user_message:
                await websocket.send_json({"type": "error", "message": "Empty message"})
                continue

            # Stream agent response
            async for event in run_stream(
                user_message=user_message,
                user_id=user_id,
                conversation_id=conversation_id,
            ):
                await websocket.send_json(event)

                # Track conversation_id for subsequent messages
                if event.get("type") == "done":
                    conversation_id = event.get("conversation_id", conversation_id)

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass
