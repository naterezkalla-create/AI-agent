"""Shared request-scoped auth helpers."""

from __future__ import annotations

from fastapi import Depends, HTTPException, Query, Request, WebSocket, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.auth import decode_token

security = HTTPBearer(auto_error=False)


def _decode_or_401(token: str | None) -> str:
    user_id = decode_token(token) if token else None
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user_id


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    token: str | None = Query(default=None),
) -> str:
    """Extract user_id from Authorization header or token query param."""
    auth = credentials
    if auth is None:
        auth = await security(request)
    if auth and auth.credentials:
        return _decode_or_401(auth.credentials)
    return _decode_or_401(token)


async def get_current_user_ws(websocket: WebSocket) -> str:
    """Extract user_id for websocket connections."""
    auth_header = websocket.headers.get("authorization", "")
    token = websocket.query_params.get("token")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
    return _decode_or_401(token)
