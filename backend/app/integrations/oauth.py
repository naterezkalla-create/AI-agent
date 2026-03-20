"""OAuth2 flow handler for Google APIs. Stores encrypted tokens in Supabase."""

import logging
from datetime import datetime, timezone
from typing import Optional, List
from urllib.parse import urlencode
from cryptography.fernet import Fernet
import httpx
from app.config import get_settings
from app.memory.supabase_client import get_supabase

logger = logging.getLogger(__name__)

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"

SCOPES = {
    "gmail": [
        "https://www.googleapis.com/auth/gmail.readonly",
        "https://www.googleapis.com/auth/gmail.send",
    ],
    "calendar": [
        "https://www.googleapis.com/auth/calendar",
        "https://www.googleapis.com/auth/calendar.events",
    ],
}


def _get_fernet() -> Fernet:
    settings = get_settings()
    if not settings.encryption_key:
        raise ValueError("ENCRYPTION_KEY not set. Generate one with: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'")
    return Fernet(settings.encryption_key.encode())


def _encrypt(value: str) -> str:
    return _get_fernet().encrypt(value.encode()).decode()


def _decrypt(value: str) -> str:
    return _get_fernet().decrypt(value.encode()).decode()


def get_authorization_url(provider: str = "google", scopes: Optional[List[str]] = None) -> str:
    """Generate OAuth2 authorization URL."""
    settings = get_settings()

    if provider != "google":
        raise ValueError(f"Unsupported provider: {provider}")

    if not settings.google_client_id:
        raise ValueError("GOOGLE_CLIENT_ID not set in environment")

    all_scopes = []
    if scopes:
        for scope_key in scopes:
            all_scopes.extend(SCOPES.get(scope_key, [scope_key]))
    else:
        for scope_list in SCOPES.values():
            all_scopes.extend(scope_list)

    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": settings.google_redirect_uri,
        "response_type": "code",
        "scope": " ".join(all_scopes),
        "access_type": "offline",
        "prompt": "consent",
    }
    query = urlencode(params)
    url = f"{GOOGLE_AUTH_URL}?{query}"
    logger.info(f"Generated OAuth URL for {provider}")
    return url


async def exchange_code(code: str, provider: str = "google") -> dict:
    """Exchange authorization code for access/refresh tokens."""
    settings = get_settings()

    async with httpx.AsyncClient() as client:
        response = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "redirect_uri": settings.google_redirect_uri,
                "grant_type": "authorization_code",
            },
        )
        response.raise_for_status()
        tokens = response.json()

    # Store encrypted tokens in Supabase
    sb = get_supabase()
    now = datetime.now(timezone.utc).isoformat()

    token_row = {
        "user_id": "default",
        "provider": provider,
        "access_token_enc": _encrypt(tokens["access_token"]),
        "refresh_token_enc": _encrypt(tokens.get("refresh_token", "")),
        "scopes": tokens.get("scope", ""),
        "expires_at": now,  # Will be updated properly based on expires_in
        "created_at": now,
    }

    # Upsert by (user_id, provider)
    existing = sb.table("integrations").select("id").eq("user_id", "default").eq("provider", provider).execute()
    if existing.data:
        sb.table("integrations").update(token_row).eq("id", existing.data[0]["id"]).execute()
    else:
        sb.table("integrations").insert(token_row).execute()

    return {"status": "connected", "provider": provider}


async def get_access_token(user_id: str, provider: str = "google") -> Optional[str]:
    """Get a valid access token, refreshing if needed."""
    sb = get_supabase()
    result = sb.table("integrations").select("*").eq("user_id", user_id).eq("provider", provider).execute()

    if not result.data:
        return None

    integration = result.data[0]
    access_token = _decrypt(integration["access_token_enc"])
    refresh_token = _decrypt(integration["refresh_token_enc"]) if integration["refresh_token_enc"] else None

    # Try refreshing the token (simple approach: always refresh)
    if refresh_token:
        settings = get_settings()
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    GOOGLE_TOKEN_URL,
                    data={
                        "client_id": settings.google_client_id,
                        "client_secret": settings.google_client_secret,
                        "refresh_token": refresh_token,
                        "grant_type": "refresh_token",
                    },
                )
                if response.status_code == 200:
                    tokens = response.json()
                    new_access = tokens["access_token"]
                    sb.table("integrations").update({
                        "access_token_enc": _encrypt(new_access),
                    }).eq("id", integration["id"]).execute()
                    return new_access
        except Exception as e:
            logger.warning(f"Token refresh failed: {e}")

    return access_token


async def list_integrations(user_id: str) -> List[dict]:
    sb = get_supabase()
    result = sb.table("integrations").select("*").eq("user_id", user_id).execute()

    integrations = []
    for row in result.data:
        status = "connected"
        last_error = None
        capabilities: list[str] = []

        try:
            access_token = await get_access_token(user_id, row["provider"])
            if not access_token:
                status = "reauth_required"
                last_error = "No valid access token available."
        except Exception as e:
            status = "error"
            last_error = str(e)

        scopes = row.get("scopes", "") or ""
        if "gmail" in scopes:
            capabilities.append("Gmail")
        if "calendar" in scopes:
            capabilities.append("Calendar")

        integrations.append({
            "id": row["id"],
            "provider": row["provider"],
            "scopes": scopes,
            "created_at": row["created_at"],
            "status": status,
            "last_checked_at": datetime.now(timezone.utc).isoformat(),
            "last_sync_at": row.get("created_at"),
            "last_error": last_error,
            "has_refresh_token": bool(row.get("refresh_token_enc")),
            "capabilities": capabilities,
        })

    return integrations


async def delete_integration(user_id: str, provider: str) -> bool:
    sb = get_supabase()
    result = sb.table("integrations").delete().eq("user_id", user_id).eq("provider", provider).execute()
    return len(result.data) > 0
