from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict
from functools import lru_cache
import os
from dotenv import load_dotenv
from pathlib import Path

# Load .env file FIRST - support both local and Docker deployments
# Try multiple locations: Docker /app/.env, local backend/.env, current directory
_env_paths = [
    Path("/app/.env"),  # Docker container
    Path(__file__).parent.parent.parent / "backend" / ".env",  # Local dev
    Path(".env"),  # Current directory
]

_env_file = None
for path in _env_paths:
    if path.exists():
        _env_file = path
        break

# Load .env into os.environ BEFORE creating Settings  
if _env_file:
    load_dotenv(_env_file, override=True)


class Settings(BaseSettings):
    # App
    app_name: str = "AI Agent"
    debug: bool = False
    api_key: str = ""

    # Anthropic
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-20250514"
    max_tokens: int = 4096

    # Supabase
    supabase_url: str = ""
    supabase_key: str = ""

    # Telegram
    telegram_bot_token: str = ""
    telegram_webhook_url: str = ""

    # Search
    tavily_api_key: str = ""

    # Google OAuth
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/integrations/google/callback"

    # Encryption
    encryption_key: str = ""

    # JWT Authentication
    jwt_secret: str = "your-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 168  # 7 days

    # Email Service
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    from_email: str = ""
    from_name: str = "AI Agent"
    frontend_url: str = "http://localhost:5173"

    # CORS
    cors_allowed_origins: str = "http://localhost:5173,http://localhost:3000,http://localhost:8000"

    # Sandbox
    sandbox_dir: str = "/tmp/agent-sandbox"

    # Scheduler
    scheduler_enabled: bool = True

    model_config = SettingsConfigDict(
        env_file=_env_file,  # Use absolute path
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
