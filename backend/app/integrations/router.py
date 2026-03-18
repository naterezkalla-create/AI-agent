from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
import logging
from app.integrations.oauth import (
    get_authorization_url,
    exchange_code,
    list_integrations,
    delete_integration,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/integrations", tags=["integrations"])


@router.get("/google/authorize")
async def google_authorize(scopes: str = "gmail,calendar"):
    """Start Google OAuth flow. Redirects user to Google consent screen."""
    try:
        scope_list = [s.strip() for s in scopes.split(",")]
        url = get_authorization_url("google", scope_list)
        logger.info(f"Redirecting to OAuth URL")
        return RedirectResponse(url)
    except Exception as e:
        logger.error(f"OAuth authorize error: {e}", exc_info=True)
        return {"error": str(e)}


@router.get("/google/callback")
async def google_callback(code: str):
    """Handle OAuth callback from Google."""
    result = await exchange_code(code, "google")
    return result


@router.get("/")
async def get_integrations():
    """List all connected integrations."""
    return await list_integrations("default")


@router.delete("/{provider}")
async def disconnect_integration(provider: str):
    """Disconnect an integration."""
    success = await delete_integration("default", provider)
    if success:
        return {"status": "disconnected", "provider": provider}
    return {"status": "not_found", "provider": provider}
