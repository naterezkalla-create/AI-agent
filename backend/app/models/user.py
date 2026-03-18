from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional


class UserCreate(BaseModel):
    """User registration request."""
    email: EmailStr
    password: str
    full_name: Optional[str] = None


class UserLogin(BaseModel):
    """User login request."""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """User response model."""
    id: str
    email: str
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    created_at: datetime
    email_verified: bool


class TokenResponse(BaseModel):
    """Authentication token response."""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class EmailVerificationRequest(BaseModel):
    """Request to send verification email."""
    pass


class VerifyEmailRequest(BaseModel):
    """Request to verify email with token."""
    token: str


class ForgotPasswordRequest(BaseModel):
    """Request password reset email."""
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Reset password with token."""
    token: str
    new_password: str
    confirm_password: str


class VerifyResetTokenRequest(BaseModel):
    """Verify password reset token is valid."""
    token: str

