from typing import Any
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
import logging
from app.api.deps import get_current_user
from app.automations.scheduler import dispatch_platform_event
from app.integrations.oauth import (
    connect_api_key_integration,
    create_custom_webhook_integration,
    test_integration_connection,
    get_authorization_url,
    exchange_code,
    list_integrations,
    list_provider_status,
    delete_integration,
    _decrypt,
)
from app.memory.supabase_client import get_supabase
from app.events.bus import event_bus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/integrations", tags=["integrations"])


class IntegrationConnectRequest(BaseModel):
    api_key: str | None = None
    config: dict[str, Any] | None = None
    label: str | None = None


def _external_base_url(request: Request) -> str:
    return str(request.base_url).rstrip("/")


@router.get("/google/authorize")
async def google_authorize(scopes: str = "gmail,calendar", user_id: str = Depends(get_current_user)):
    """Start Google OAuth flow. Redirects user to Google consent screen."""
    try:
        scope_list = [s.strip() for s in scopes.split(",")]
        url = get_authorization_url("google", scope_list, state=user_id)
        logger.info(f"Redirecting to OAuth URL")
        return RedirectResponse(url)
    except Exception as e:
        logger.error(f"OAuth authorize error: {e}", exc_info=True)
        return {"error": str(e)}


@router.get("/google/callback")
async def google_callback(code: str, state: str | None = None):
    """Handle OAuth callback from Google."""
    user_id = state or "default"
    result = await exchange_code(code, "google", user_id=user_id)
    await event_bus.publish(
        "integrations.changed",
        {"provider": "google", "status": "connected"},
        topics={"integrations"},
    )
    await dispatch_platform_event(
        "integrations.changed",
        user_id,
        {"provider": "google", "status": "connected"},
    )
    return result


@router.get("/")
async def get_integrations(user_id: str = Depends(get_current_user)):
    """List all connected integrations."""
    return await list_integrations(user_id)


@router.get("/providers")
async def get_providers(user_id: str = Depends(get_current_user)):
    """List all supported providers with registry metadata and status."""
    return await list_provider_status(user_id)


@router.post("/{provider}/connect")
async def connect_integration(
    provider: str,
    payload: IntegrationConnectRequest,
    request: Request,
    user_id: str = Depends(get_current_user),
):
    if provider == "google":
        raise HTTPException(status_code=400, detail="Google uses OAuth authorization")
    if provider == "custom_webhook":
        result = await create_custom_webhook_integration(
            user_id,
            base_url=_external_base_url(request),
            label=payload.label,
        )
    else:
        if not payload.api_key:
            raise HTTPException(status_code=400, detail="API key is required")
        result = await connect_api_key_integration(
            user_id,
            provider,
            payload.api_key,
            payload.config,
        )

    await event_bus.publish(
        "integrations.changed",
        {"provider": provider, "status": "connected"},
        user_id=user_id,
        topics={"integrations"},
    )
    await dispatch_platform_event(
        "integrations.changed",
        user_id,
        {"provider": provider, "status": "connected"},
    )
    return result


@router.post("/{provider}/test")
async def test_integration(
    provider: str,
    payload: IntegrationConnectRequest,
    user_id: str = Depends(get_current_user),
):
    try:
        health = await test_integration_connection(
            user_id=user_id,
            provider=provider,
            api_key=payload.api_key,
            config=payload.config,
        )
        await event_bus.publish(
            "integrations.changed",
            {"provider": provider, "status": "connected"},
            user_id=user_id,
            topics={"integrations"},
        )
        return {"status": "ok", "provider": provider, "health": health}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/{provider}")
async def disconnect_integration(provider: str, user_id: str = Depends(get_current_user)):
    """Disconnect an integration."""
    success = await delete_integration(user_id, provider)
    if success:
        await event_bus.publish(
            "integrations.changed",
            {"provider": provider, "status": "disconnected"},
            topics={"integrations"},
        )
        await dispatch_platform_event(
            "integrations.changed",
            user_id,
            {"provider": provider, "status": "disconnected"},
        )
        return {"status": "disconnected", "provider": provider}
    return {"status": "not_found", "provider": provider}


@router.post("/webhook/custom/{integration_id}")
async def custom_webhook(
    integration_id: str,
    request: Request,
    secret: str | None = None,
):
    sb = get_supabase()
    result = (
        sb.table("integrations")
        .select("*")
        .eq("id", integration_id)
        .eq("provider", "custom_webhook")
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Webhook integration not found")

    integration = result.data[0]
    header_secret = request.headers.get("X-Webhook-Secret")
    expected_secret = _decrypt(integration["access_token_enc"])
    if (secret or header_secret) != expected_secret:
        raise HTTPException(status_code=401, detail="Invalid webhook secret")

    try:
        body = await request.json()
    except Exception:
        body = {"raw": (await request.body()).decode(errors="ignore")}
    now = datetime.now(timezone.utc).isoformat()
    config = integration.get("config") or {}
    config["last_event_at"] = now
    config["last_payload_preview"] = body if isinstance(body, dict) else {"received": True}
    sb.table("integrations").update(
        {
            "config": config,
            "status": "connected",
            "last_checked_at": now,
            "last_sync_at": now,
            "last_error": None,
        }
    ).eq("id", integration_id).execute()

    payload = {
        "provider": "custom_webhook",
        "integration_id": integration_id,
        "body": body,
        "headers": dict(request.headers),
    }
    await event_bus.publish(
        "integrations.webhook.received",
        payload,
        user_id=integration["user_id"],
        topics={"integrations"},
    )
    await dispatch_platform_event(
        "integrations.webhook.received",
        integration["user_id"],
        payload,
    )
    return {"status": "accepted"}
