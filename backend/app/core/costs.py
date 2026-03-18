"""Cost tracking for API usage."""

import logging
from datetime import datetime, timezone
from typing import Optional
from app.memory.supabase_client import get_supabase

logger = logging.getLogger(__name__)

# Pricing for Claude models (prices per 1M tokens)
PRICING = {
    "claude-sonnet-4-20250514": {
        "input": 3.0,      # $3 per 1M input tokens
        "output": 15.0,    # $15 per 1M output tokens
    },
    "claude-opus": {
        "input": 15.0,
        "output": 75.0,
    },
    "claude-haiku": {
        "input": 0.80,
        "output": 4.0,
    },
}

# Default pricing if model not found
DEFAULT_PRICING = {
    "input": 3.0,
    "output": 15.0,
}


async def log_api_cost(
    user_id: str,
    service: str,
    operation: str,
    input_tokens: int = 0,
    output_tokens: int = 0,
    cost: float = 0.0,
    metadata: Optional[dict] = None,
) -> None:
    """
    Log API usage and cost to database.
    
    Args:
        user_id: User ID
        service: Service name (e.g., "claude", "gmail", "calendar")
        operation: Operation name (e.g., "chat", "send_email", "create_event")
        input_tokens: Number of input tokens (for LLM)
        output_tokens: Number of output tokens (for LLM)
        cost: Cost in dollars
        metadata: Additional metadata to store
    """
    try:
        supabase = get_supabase()
        
        now = datetime.now(timezone.utc).isoformat()
        
        data = {
            "user_id": user_id,
            "service": service,
            "operation": operation,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "cost": cost,
            "metadata": metadata or {},
            "created_at": now,
        }
        
        supabase.table("cost_logs").insert(data).execute()
        logger.debug(f"Logged cost: {service} {operation} - ${cost:.6f}")
        
    except Exception as e:
        logger.error(f"Failed to log cost: {e}")


def calculate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Calculate cost for Claude API call."""
    pricing = PRICING.get(model, DEFAULT_PRICING)
    
    input_cost = (input_tokens / 1_000_000) * pricing["input"]
    output_cost = (output_tokens / 1_000_000) * pricing["output"]
    
    return input_cost + output_cost


async def get_user_costs(user_id: str, days: int = 30) -> dict:
    """Get cost summary for a user over the past N days."""
    try:
        supabase = get_supabase()
        
        # Query costs from the past N days
        from datetime import timedelta
        start_date = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        
        result = supabase.table("cost_logs").select("*").gte("created_at", start_date).eq("user_id", user_id).execute()
        
        logs = result.data or []
        
        # Calculate totals
        total_cost = sum(log["cost"] for log in logs)
        total_tokens = sum(log["total_tokens"] for log in logs)
        
        # Group by service
        by_service = {}
        for log in logs:
            service = log["service"]
            if service not in by_service:
                by_service[service] = {
                    "cost": 0.0,
                    "tokens": 0,
                    "operations": 0,
                }
            by_service[service]["cost"] += log["cost"]
            by_service[service]["tokens"] += log["total_tokens"]
            by_service[service]["operations"] += 1
        
        # Group by date for trend
        by_date = {}
        for log in logs:
            date = log["created_at"][:10]  # YYYY-MM-DD
            if date not in by_date:
                by_date[date] = 0.0
            by_date[date] += log["cost"]
        
        return {
            "total_cost": round(total_cost, 6),
            "total_tokens": total_tokens,
            "total_operations": len(logs),
            "by_service": by_service,
            "by_date": dict(sorted(by_date.items())),
            "days": days,
        }
        
    except Exception as e:
        logger.error(f"Failed to get costs: {e}")
        return {
            "total_cost": 0.0,
            "total_tokens": 0,
            "total_operations": 0,
            "by_service": {},
            "by_date": {},
            "days": days,
        }
