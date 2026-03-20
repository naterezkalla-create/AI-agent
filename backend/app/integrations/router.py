from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
import logging
from app.api.deps import get_current_user
from app.automations.scheduler import dispatch_platform_event
from app.integrations.oauth import (
    get_authorization_url,
    exchange_code,
    list_integrations,
    list_provider_status,
    delete_integration,
)
from app.events.bus import event_bus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/integrations", tags=["integrations"])


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
