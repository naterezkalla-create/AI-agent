import jwt
import hashlib
import os
import secrets
from datetime import datetime, timedelta
from typing import Optional
from app.config import get_settings

settings = get_settings()


def validate_password(password: str):
    """
    Validate password meets minimum security requirements.
    Returns (is_valid, error_message)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"
    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one number"
    if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
        return False, "Password must contain at least one special character (!@#$%^&*)"
    return True, ""


def hash_password(password: str) -> str:
    """Hash a password using PBKDF2."""
    salt = os.urandom(32).hex()
    pwd_hash = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100000)
    return f"{salt}${pwd_hash.hex()}"


def verify_password(password: str, hash_value: str) -> bool:
    """Verify a password against a hash."""
    try:
        salt, pwd_hash = hash_value.split("$")
        new_hash = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100000).hex()
        return new_hash == pwd_hash
    except Exception:
        return False


def create_access_token(user_id: str) -> str:
    """Create a JWT access token."""
    payload = {
        "sub": user_id,
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(hours=settings.jwt_expiration_hours),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> Optional[str]:
    """Decode and verify a JWT token, returning the user_id."""
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        return payload.get("sub")
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def generate_token(length: int = 32) -> str:
    """Generate a secure random token for email verification or password reset."""
    return secrets.token_urlsafe(length)


def hash_token(token: str) -> str:
    """Hash a token for secure storage in the database."""
    return hashlib.sha256(token.encode()).hexdigest()


def verify_token(token: str, token_hash: str) -> bool:
    """Verify a token against its stored hash."""
    return hashlib.sha256(token.encode()).hexdigest() == token_hash

