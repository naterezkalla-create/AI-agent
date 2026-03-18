import anthropic
import logging
from typing import AsyncIterator, Optional, List
from app.config import get_settings
from app.core.costs import log_api_cost, calculate_cost
from app.memory.supabase_client import get_supabase
from app.core.encryption import decrypt_api_key

logger = logging.getLogger(__name__)


def _get_api_key(user_id: str = "default") -> str:
    """Get API key for user, with fallback to default settings."""
    try:
        sb = get_supabase()
        result = sb.table("user_settings").select("api_keys").eq("user_id", user_id).execute()
        
        if result.data and result.data[0].get("api_keys", {}).get("anthropic"):
            encrypted_key = result.data[0]["api_keys"]["anthropic"]
            try:
                return decrypt_api_key(encrypted_key)
            except Exception as e:
                logger.warning(f"Failed to decrypt user API key for {user_id}, falling back to default: {str(e)}")
    except Exception as e:
        logger.warning(f"Failed to retrieve user API key for {user_id}: {str(e)}")
    
    # Fall back to default API key from settings
    settings = get_settings()
    return settings.anthropic_api_key


def get_client(api_key: Optional[str] = None) -> anthropic.AsyncAnthropic:
    if api_key is None:
        api_key = get_settings().anthropic_api_key
    return anthropic.AsyncAnthropic(api_key=api_key)


async def chat(
    messages: List[dict],
    system: str,
    tools: Optional[List[dict]] = None,
    model: Optional[str] = None,
    max_tokens: Optional[int] = None,
    user_id: str = "default",
) -> anthropic.types.Message:
    """Send a message to Claude and return the full response."""
    settings = get_settings()
    
    # Get user-specific API key or fall back to default
    api_key = _get_api_key(user_id)
    client = get_client(api_key)
    
    model_name = model or settings.anthropic_model

    kwargs: dict = {
        "model": model_name,
        "max_tokens": max_tokens or settings.max_tokens,
        "system": system,
        "messages": messages,
    }
    if tools:
        kwargs["tools"] = tools

    response = await client.messages.create(**kwargs)
    
    # Log cost if usage info is available
    if hasattr(response, 'usage'):
        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens
        cost = calculate_cost(model_name, input_tokens, output_tokens)
        
        await log_api_cost(
            user_id=user_id,
            service="claude",
            operation="chat",
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost=cost,
            metadata={"model": model_name}
        )
    
    return response


async def chat_stream(
    messages: List[dict],
    system: str,
    tools: Optional[List[dict]] = None,
    model: Optional[str] = None,
    max_tokens: Optional[int] = None,
    user_id: str = "default",
) -> AsyncIterator:
    """Stream a response from Claude. Yields raw stream events."""
    settings = get_settings()
    
    # Get user-specific API key or fall back to default
    api_key = _get_api_key(user_id)
    client = get_client(api_key)

    kwargs: dict = {
        "model": model or settings.anthropic_model,
        "max_tokens": max_tokens or settings.max_tokens,
        "system": system,
        "messages": messages,
    }
    if tools:
        kwargs["tools"] = tools

    async with client.messages.stream(**kwargs) as stream:
        async for event in stream:
            yield event
