"""Encryption utilities for storing and retrieving sensitive API keys."""

from cryptography.fernet import Fernet, InvalidToken
from app.config import get_settings
import logging

logger = logging.getLogger(__name__)


def _get_fernet() -> Fernet:
    """Get Fernet cipher instance using encryption key from settings."""
    settings = get_settings()
    if not settings.encryption_key:
        raise ValueError(
            "ENCRYPTION_KEY not set. Generate one with: "
            "python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'"
        )
    return Fernet(settings.encryption_key.encode())


def encrypt_api_key(key: str) -> str:
    """Encrypt an API key for secure storage."""
    try:
        encrypted = _get_fernet().encrypt(key.encode()).decode()
        return encrypted
    except Exception as e:
        logger.error(f"Failed to encrypt API key: {str(e)}")
        raise ValueError("Failed to encrypt API key")


def decrypt_api_key(encrypted_key: str) -> str:
    """Decrypt an API key from storage."""
    try:
        decrypted = _get_fernet().decrypt(encrypted_key.encode()).decode()
        return decrypted
    except InvalidToken:
        logger.error("Invalid or corrupted API key")
        raise ValueError("Invalid or corrupted API key in storage")
    except Exception as e:
        logger.error(f"Failed to decrypt API key: {str(e)}")
        raise ValueError("Failed to decrypt API key")
