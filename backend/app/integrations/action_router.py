from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.deps import get_current_user
from app.integrations.action_service import (
    approve_action_request,
    create_action_request,
    list_action_catalog,
    list_action_requests,
    list_external_resources,
    reject_action_request,
)

router = APIRouter(prefix="/api/external-actions", tags=["external-actions"])


class ExternalActionRequestCreate(BaseModel):
    provider: str
    action_name: str
    payload: dict[str, Any]
    auto_execute: bool = False


@router.get("/catalog")
async def get_catalog(user_id: str = Depends(get_current_user)):
    return await list_action_catalog()


@router.get("/requests")
async def get_requests(status: str | None = None, user_id: str = Depends(get_current_user)):
    return await list_action_requests(user_id, status=status)


@router.post("/requests")
async def create_request(body: ExternalActionRequestCreate, user_id: str = Depends(get_current_user)):
    return await create_action_request(
        user_id=user_id,
        provider=body.provider,
        action_name=body.action_name,
        payload=body.payload,
        requested_by="user",
        auto_execute=body.auto_execute,
    )


@router.post("/requests/{request_id}/approve")
async def approve_request(request_id: str, user_id: str = Depends(get_current_user)):
    return await approve_action_request(request_id, user_id)


@router.post("/requests/{request_id}/reject")
async def reject_request(request_id: str, user_id: str = Depends(get_current_user)):
    return await reject_action_request(request_id, user_id)


@router.get("/resources")
async def get_resources(provider: str | None = None, user_id: str = Depends(get_current_user)):
    return await list_external_resources(user_id, provider=provider)
