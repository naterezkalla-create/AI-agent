"""Cost tracking API endpoints."""

from fastapi import APIRouter, Query
from app.core.costs import get_user_costs

router = APIRouter(prefix="/api/costs", tags=["costs"])


@router.get("/summary")
async def get_cost_summary(user_id: str = "default", days: int = Query(30, ge=1, le=365)):
    """Get cost summary for a user over the past N days."""
    return await get_user_costs(user_id, days)


@router.get("/breakdown")
async def get_cost_breakdown(user_id: str = "default", days: int = Query(30, ge=1, le=365)):
    """Get detailed cost breakdown by service."""
    return await get_user_costs(user_id, days)
