"""FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.api.auth import AuthMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from app.api.chat import router as chat_router
from app.api.admin import router as admin_router
from app.api.costs import router as costs_router
from app.api.settings import router as settings_router
from app.api.users import router as users_router
from app.entities.router import router as entities_router
from app.automations.router import router as automations_router
from app.integrations.router import router as integrations_router
from app.channels.telegram import router as telegram_router
from app.channels.websocket import router as websocket_router
from app.tools.registry import register_all_tools
from app.logging_config import setup_logging, get_logger

# Setup structured logging
settings_temp = get_settings()
setup_logging(debug=settings_temp.debug)
logger = get_logger(__name__)

# Rate limiter
limiter = Limiter(key_func=get_remote_address)


async def rate_limit_exceeded_handler(request, exc):
    """Handle rate limit exceeded errors."""
    return JSONResponse(
        status_code=429,
        content={"detail": "Too many requests. Please try again later."},
    )


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers to all responses."""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Content Security Policy - restrict to same origin + trusted sources
        # Allows self, inline styles for Tailwind, and Google fonts
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: https:; "
            "connect-src 'self' https:; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )
        
        # Prevent clickjacking attacks
        response.headers["X-Frame-Options"] = "DENY"
        
        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # Enable XSS protection in older browsers
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Enforce HTTPS for future requests
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # Disable caching for sensitive data
        response.headers["Cache-Control"] = "no-store, max-age=0"
        
        # Referrer policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Permissions policy (formerly Feature-Policy)
        response.headers["Permissions-Policy"] = (
            "accelerometer=(), "
            "camera=(), "
            "geolocation=(), "
            "gyroscope=(), "
            "magnetometer=(), "
            "microphone=(), "
            "payment=(), "
            "usb=()"
        )
        
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    settings = get_settings()

    # Register all tools
    register_all_tools()
    logger.info("All tools registered")

    # Start scheduler
    if settings.scheduler_enabled:
        from app.automations.scheduler import start_scheduler, load_automations, stop_scheduler
        start_scheduler()
        await load_automations()
        logger.info("Scheduler started and automations loaded")

    # Setup Telegram webhook (or polling for local dev)
    if settings.telegram_bot_token:
        from app.channels.telegram import setup_webhook
        try:
            await setup_webhook()
        except Exception as e:
            logger.warning(f"Failed to setup Telegram: {e}")

    logger.info(f"🚀 {settings.app_name} is ready!")

    yield

    # Shutdown
    if settings.scheduler_enabled:
        from app.automations.scheduler import stop_scheduler
        stop_scheduler()
    
    # Stop Telegram polling
    from app.channels.telegram import stop_polling
    await stop_polling()
    
    logger.info("Shutdown complete")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        description="AI Agent powered by Claude — with tools, memory, CRM, automations, and integrations.",
        version="1.0.0",
        lifespan=lifespan,
    )

    # Rate limiting
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

    # CORS - Restrict to specific origins
    allowed_origins = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://localhost:8000",
    ]
    if not settings.debug:
        # Add production domains here
        allowed_origins.extend([
            # "https://yourdomain.com",
        ])

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    # Auth
    app.add_middleware(AuthMiddleware)
    
    # Security Headers
    app.add_middleware(SecurityHeadersMiddleware)

    # Routers
    app.include_router(chat_router)
    app.include_router(admin_router)
    app.include_router(costs_router)
    app.include_router(settings_router)
    app.include_router(users_router)
    app.include_router(entities_router)
    app.include_router(automations_router)
    app.include_router(integrations_router)
    app.include_router(telegram_router)
    app.include_router(websocket_router)

    @app.get("/")
    async def root():
        return {"name": settings.app_name, "status": "running"}

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    return app


app = create_app()
