"""API key authentication middleware."""

import logging
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from app.config import get_settings

logger = logging.getLogger(__name__)

# Exact paths that don't require auth.
PUBLIC_PATHS = {
    "/",
    "/health",
    "/ready",
    "/docs",
    "/openapi.json",
    "/redoc",
    "/webhook/telegram",
    "/integrations/google/callback",
    "/integrations/webhook/custom",
}

# Prefixes that don't require auth.
PUBLIC_PREFIXES = (
    "/api/auth/",
    "/ws/",
)


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        settings = get_settings()

        # Skip auth if no API key configured (dev mode)
        api_key = settings.api_key.strip() if settings.api_key else ""
        if not api_key:
            return await call_next(request)

        # Skip auth for public paths (prefix matching)
        path = request.url.path
        if path in PUBLIC_PATHS:
            return await call_next(request)
        for prefix in PUBLIC_PREFIXES:
            if path.startswith(prefix):
                return await call_next(request)

        # Check Authorization header
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            if token == api_key:
                return await call_next(request)

        raise HTTPException(status_code=401, detail="Invalid or missing API key")
