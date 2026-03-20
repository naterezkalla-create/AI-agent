"""Integration connection and token management."""

import logging
import secrets
from datetime import datetime, timezone
from typing import Any, Optional, List
from urllib.parse import urlencode
from cryptography.fernet import Fernet
import httpx
from app.config import get_settings
from app.integrations.providers import PROVIDER_REGISTRY, list_provider_definitions
from app.memory.supabase_client import get_supabase

logger = logging.getLogger(__name__)

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
NOTION_VERSION = "2022-06-28"

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


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _get_integration_row(user_id: str, provider: str) -> dict[str, Any] | None:
    sb = get_supabase()
    result = sb.table("integrations").select("*").eq("user_id", user_id).eq("provider", provider).execute()
    return result.data[0] if result.data else None


async def _store_integration(
    *,
    user_id: str,
    provider: str,
    access_secret: str,
    refresh_secret: str | None = None,
    scopes: str = "",
    config: dict[str, Any] | None = None,
    status: str = "connected",
    last_error: str | None = None,
) -> dict[str, Any]:
    sb = get_supabase()
    now = _iso_now()
    payload = {
        "user_id": user_id,
        "provider": provider,
        "access_token_enc": _encrypt(access_secret),
        "refresh_token_enc": _encrypt(refresh_secret) if refresh_secret else None,
        "scopes": scopes,
        "config": config or {},
        "status": status,
        "last_checked_at": now,
        "last_sync_at": now,
        "last_error": last_error,
        "expires_at": now,
        "created_at": now,
    }
    existing = _get_integration_row(user_id, provider)
    if existing:
        result = sb.table("integrations").update(payload).eq("id", existing["id"]).execute()
        return result.data[0]
    result = sb.table("integrations").insert(payload).execute()
    return result.data[0]


async def _update_integration_status(
    *,
    user_id: str,
    provider: str,
    status: str,
    last_error: str | None = None,
    config: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    sb = get_supabase()
    existing = _get_integration_row(user_id, provider)
    if not existing:
        return None
    payload: dict[str, Any] = {
        "status": status,
        "last_error": last_error,
        "last_checked_at": _iso_now(),
    }
    if config is not None:
        payload["config"] = config
    result = sb.table("integrations").update(payload).eq("id", existing["id"]).execute()
    return result.data[0] if result.data else existing


def _capabilities_to_scopes(provider: str) -> str:
    return " ".join(PROVIDER_REGISTRY.get(provider, {}).get("capabilities", []))


async def _test_slack(api_key: str) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(
            "https://slack.com/api/auth.test",
            headers={"Authorization": f"Bearer {api_key}"},
        )
        data = response.json()
        if response.status_code != 200 or not data.get("ok"):
            raise ValueError(data.get("error", "Slack authentication failed"))
        return {
            "workspace": data.get("team"),
            "workspace_id": data.get("team_id"),
            "bot_user_id": data.get("user_id"),
            "url": data.get("url"),
        }


async def _test_github(api_key: str) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(
            "https://api.github.com/user",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Accept": "application/vnd.github+json",
            },
        )
        if response.status_code != 200:
            raise ValueError("GitHub authentication failed")
        data = response.json()
        return {
            "login": data.get("login"),
            "name": data.get("name"),
            "avatar_url": data.get("avatar_url"),
        }


async def _test_notion(api_key: str) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(
            "https://api.notion.com/v1/users/me",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Notion-Version": NOTION_VERSION,
            },
        )
        if response.status_code != 200:
            raise ValueError("Notion authentication failed")
        data = response.json()
        bot = data.get("bot", {})
        owner = data.get("owner", {})
        return {
            "workspace_name": bot.get("workspace_name"),
            "owner_type": owner.get("type"),
            "bot_id": data.get("id"),
        }


async def _test_apify(api_key: str) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(
            "https://api.apify.com/v2/users/me",
            params={"token": api_key},
        )
        if response.status_code != 200:
            raise ValueError("Apify authentication failed")
        data = response.json().get("data", {})
        return {
            "username": data.get("username"),
            "email": data.get("email"),
            "plan": data.get("plan"),
        }


async def connect_api_key_integration(
    user_id: str,
    provider: str,
    api_key: str,
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    provider_def = PROVIDER_REGISTRY.get(provider)
    if not provider_def or provider_def.get("connection_mode") not in {"api_key", "env_or_api_key"}:
        raise ValueError(f"Provider {provider} does not support API key connections")

    health = await test_integration_connection(
        user_id=user_id,
        provider=provider,
        api_key=api_key,
        config=config,
        persist=False,
    )
    stored = await _store_integration(
        user_id=user_id,
        provider=provider,
        access_secret=api_key,
        scopes=_capabilities_to_scopes(provider),
        config={**(config or {}), "health": health},
    )
    return {
        "status": "connected",
        "provider": provider,
        "integration": stored,
        "health": health,
    }


async def create_custom_webhook_integration(
    user_id: str,
    *,
    base_url: str,
    label: str | None = None,
) -> dict[str, Any]:
    secret = secrets.token_urlsafe(24)
    config = {
        "label": label or "Webhook endpoint",
    }
    stored = await _store_integration(
        user_id=user_id,
        provider="custom_webhook",
        access_secret=secret,
        scopes=_capabilities_to_scopes("custom_webhook"),
        config=config,
    )
    webhook_url = f"{base_url.rstrip('/')}/integrations/webhook/custom/{stored['id']}"
    config["webhook_url"] = webhook_url
    stored = await _update_integration_status(
        user_id=user_id,
        provider="custom_webhook",
        status="connected",
        config=config,
    ) or stored
    return {
        "status": "connected",
        "provider": "custom_webhook",
        "integration": stored,
        "webhook_url": webhook_url,
    }


def get_authorization_url(provider: str = "google", scopes: Optional[List[str]] = None, state: Optional[str] = None) -> str:
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
    if state:
        params["state"] = state
    query = urlencode(params)
    url = f"{GOOGLE_AUTH_URL}?{query}"
    logger.info(f"Generated OAuth URL for {provider}")
    return url


async def exchange_code(code: str, provider: str = "google", user_id: str = "default") -> dict:
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
        "user_id": user_id,
        "provider": provider,
        "access_token_enc": _encrypt(tokens["access_token"]),
        "refresh_token_enc": _encrypt(tokens.get("refresh_token", "")) if tokens.get("refresh_token") else None,
        "scopes": tokens.get("scope", ""),
        "expires_at": now,
        "created_at": now,
        "status": "connected",
        "last_checked_at": now,
        "last_sync_at": now,
        "last_error": None,
    }

    existing = sb.table("integrations").select("id").eq("user_id", user_id).eq("provider", provider).execute()
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


async def get_provider_secret(user_id: str, provider: str) -> Optional[str]:
    """Return the decrypted stored secret for a provider."""
    row = _get_integration_row(user_id, provider)
    if not row or not row.get("access_token_enc"):
        return None
    return _decrypt(row["access_token_enc"])


async def list_integrations(user_id: str) -> List[dict]:
    sb = get_supabase()
    result = sb.table("integrations").select("*").eq("user_id", user_id).execute()

    integrations = []
    for row in result.data:
        provider = row["provider"]
        status = row.get("status") or "connected"
        last_error = row.get("last_error")
        capabilities: list[str] = []

        if provider == "google":
            try:
                access_token = await get_access_token(user_id, provider)
                if not access_token:
                    status = "reauth_required"
                    last_error = "No valid access token available."
            except Exception as e:
                status = "error"
                last_error = str(e)

        scopes = row.get("scopes", "") or ""
        if provider == "google":
            if "gmail" in scopes:
                capabilities.append("Gmail")
            if "calendar" in scopes:
                capabilities.append("Calendar")
        else:
            capabilities = PROVIDER_REGISTRY.get(provider, {}).get("capabilities", [])

        config = row.get("config") or {}

        integrations.append({
            "id": row["id"],
            "provider": provider,
            "scopes": scopes,
            "created_at": row["created_at"],
            "status": status,
            "last_checked_at": row.get("last_checked_at") or datetime.now(timezone.utc).isoformat(),
            "last_sync_at": row.get("last_sync_at") or row.get("created_at"),
            "last_error": last_error,
            "has_refresh_token": bool(row.get("refresh_token_enc")),
            "capabilities": capabilities,
            "config": {
                **config,
                "secret_configured": bool(row.get("access_token_enc")),
                **({"webhook_url": config.get("webhook_url")} if config.get("webhook_url") else {}),
            },
        })

    return integrations


async def delete_integration(user_id: str, provider: str) -> bool:
    sb = get_supabase()
    result = sb.table("integrations").delete().eq("user_id", user_id).eq("provider", provider).execute()
    return len(result.data) > 0


async def test_integration_connection(
    *,
    user_id: str,
    provider: str,
    api_key: str | None = None,
    config: dict[str, Any] | None = None,
    persist: bool = True,
) -> dict[str, Any]:
    if provider == "google":
        access_token = await get_access_token(user_id, provider)
        if not access_token:
            raise ValueError("Google integration is not connected")
        health = {"status": "connected", "provider": "google"}
    elif provider == "slack":
        if not api_key:
            existing = _get_integration_row(user_id, provider)
            api_key = _decrypt(existing["access_token_enc"]) if existing else None
        if not api_key:
            raise ValueError("Slack token is required")
        health = await _test_slack(api_key)
    elif provider == "github":
        if not api_key:
            existing = _get_integration_row(user_id, provider)
            api_key = _decrypt(existing["access_token_enc"]) if existing else None
        if not api_key:
            raise ValueError("GitHub token is required")
        health = await _test_github(api_key)
    elif provider == "notion":
        if not api_key:
            existing = _get_integration_row(user_id, provider)
            api_key = _decrypt(existing["access_token_enc"]) if existing else None
        if not api_key:
            raise ValueError("Notion API key is required")
        health = await _test_notion(api_key)
    elif provider == "apify":
        if not api_key:
            existing = _get_integration_row(user_id, provider)
            api_key = _decrypt(existing["access_token_enc"]) if existing else None
        if not api_key:
            raise ValueError("Apify API key is required")
        health = await _test_apify(api_key)
    elif provider == "custom_webhook":
        existing = _get_integration_row(user_id, provider)
        if not existing:
            raise ValueError("Custom webhook is not configured")
        existing_config = existing.get("config") or {}
        health = {
            "webhook_url": existing_config.get("webhook_url"),
            "last_event_at": existing_config.get("last_event_at"),
            "label": existing_config.get("label"),
            "secret_configured": bool(existing.get("access_token_enc")),
        }
    else:
        raise ValueError(f"Unsupported provider: {provider}")

    if persist:
        existing = _get_integration_row(user_id, provider)
        existing_config = existing.get("config") if existing else {}
        await _update_integration_status(
            user_id=user_id,
            provider=provider,
            status="connected",
            last_error=None,
            config={**(existing_config or {}), **(config or {}), "health": health},
        )

    return health


async def list_provider_status(user_id: str) -> List[dict]:
    """Return registry-backed provider metadata merged with connection status."""
    connected = {item["provider"]: item for item in await list_integrations(user_id)}
    providers = []

    for provider in list_provider_definitions():
        connection = connected.get(provider["id"])
        providers.append(
            {
                **provider,
                "connected": bool(connection),
                "integration": connection,
                "status": connection.get("status") if connection else ("configured" if provider["is_env_ready"] else "not_configured"),
                "last_error": connection.get("last_error") if connection else None,
                "last_sync_at": connection.get("last_sync_at") if connection else None,
            }
        )

    return providers
