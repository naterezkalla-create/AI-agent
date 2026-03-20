from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.core.auth import (
    hash_password, verify_password, create_access_token, decode_token, validate_password,
    generate_token, hash_token, verify_token
)
from app.models.user import (
    UserCreate, UserLogin, UserResponse, TokenResponse,
    EmailVerificationRequest, VerifyEmailRequest, ForgotPasswordRequest,
    ResetPasswordRequest, VerifyResetTokenRequest
)
from app.memory.supabase_client import get_supabase
from app.services.email import get_email_service
from app.config import get_settings
from app.api.deps import get_current_user
from datetime import datetime, timedelta
import uuid

router = APIRouter(prefix="/api/auth", tags=["auth"])
limiter = Limiter(key_func=get_remote_address)
@router.post("/register", response_model=TokenResponse)
@limiter.limit("5/minute")
async def register(request: Request, user_data: UserCreate):
    """Register a new user with rate limiting (5 per minute)."""
    supabase = get_supabase()
    
    # Validate password strength
    is_valid, error_msg = validate_password(user_data.password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    
    # Check if user already exists
    existing = supabase.table("users").select("id").eq("email", user_data.email).execute()
    if existing.data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user
    user_id = str(uuid.uuid4())
    password_hash = hash_password(user_data.password)
    
    user_response = supabase.table("users").insert({
        "id": user_id,
        "email": user_data.email,
        "password_hash": password_hash,
        "full_name": user_data.full_name or "",
        "is_active": True,
        "email_verified": False,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }).execute()
    
    if not user_response.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )
    
    # Create default user_settings record
    supabase.table("user_settings").insert({
        "user_id": user_id,
        "user_id_fk": user_id,
        "system_prompt": "",
        "enabled_integrations": [],
        "preferences": {},
        "api_keys": {},
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }).execute()
    
    # Generate token
    token = create_access_token(user_id)
    
    return TokenResponse(
        access_token=token,
        user=UserResponse(
            id=user_id,
            email=user_data.email,
            full_name=user_data.full_name,
            avatar_url=None,
            created_at=datetime.utcnow(),
            email_verified=False,
        )
    )


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
async def login(request: Request, credentials: UserLogin):
    """Login with email and password (10 per minute rate limit)."""
    supabase = get_supabase()
    
    # Find user - select only needed fields for faster query
    result = supabase.table("users").select(
        "id, email, password_hash, full_name, avatar_url, created_at, email_verified"
    ).eq("email", credentials.email).execute()
    
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    user = result.data[0]
    
    # Verify password
    if not verify_password(credentials.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Generate token
    token = create_access_token(user["id"])
    
    # Note: Removed last_login update to reduce database calls
    # This can be tracked asynchronously if needed
    
    return TokenResponse(
        access_token=token,
        user=UserResponse(
            id=user["id"],
            email=user["email"],
            full_name=user.get("full_name"),
            avatar_url=user.get("avatar_url"),
            created_at=datetime.fromisoformat(user["created_at"]),
            email_verified=user.get("email_verified", False),
        )
    )


@router.get("/me", response_model=UserResponse)
async def get_profile(user_id: str = Depends(get_current_user)):
    """Get current user profile."""
    supabase = get_supabase()
    
    # Select only needed fields for faster query
    result = supabase.table("users").select(
        "id, email, full_name, avatar_url, created_at, email_verified"
    ).eq("id", user_id).execute()
    
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user = result.data[0]
    return UserResponse(
        id=user["id"],
        email=user["email"],
        full_name=user.get("full_name"),
        avatar_url=user.get("avatar_url"),
        created_at=datetime.fromisoformat(user["created_at"]),
        email_verified=user.get("email_verified", False),
    )


@router.put("/me", response_model=UserResponse)
async def update_profile(profile_update: dict, user_id: str = Depends(get_current_user)):
    """Update current user profile."""
    supabase = get_supabase()
    
    # Only allow specific fields to be updated
    allowed_fields = {"full_name", "avatar_url"}
    update_data = {k: v for k, v in profile_update.items() if k in allowed_fields}
    update_data["updated_at"] = datetime.utcnow().isoformat()
    
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid fields to update"
        )
    
    result = supabase.table("users").update(update_data).eq("id", user_id).execute()
    
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user = result.data[0]
    return UserResponse(
        id=user["id"],
        email=user["email"],
        full_name=user.get("full_name"),
        avatar_url=user.get("avatar_url"),
        created_at=datetime.fromisoformat(user["created_at"]),
        email_verified=user.get("email_verified", False),
    )


@router.post("/send-verification-email")
@limiter.limit("3/minute")
async def send_verification_email(request: Request, user_id: str = Depends(get_current_user)):
    """Send email verification link to current user."""
    supabase = get_supabase()
    
    # Get user
    result = supabase.table("users").select("*").eq("id", user_id).execute()
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user = result.data[0]
    
    # Check if already verified
    if user.get("email_verified_at"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already verified"
        )
    
    # Generate verification token
    token = generate_token(32)
    token_hash = hash_token(token)
    expires_at = (datetime.utcnow() + timedelta(hours=24)).isoformat()
    
    # Store token in database
    supabase.table("users").update({
        "verification_token": token_hash,
        "verification_token_expires": expires_at,
        "updated_at": datetime.utcnow().isoformat(),
    }).eq("id", user_id).execute()
    
    # Send verification email
    settings = get_settings()
    email_service = get_email_service()
    email_service.send_verification_email(
        user["email"],
        user.get("full_name"),
        token,
        frontend_url=settings.frontend_url
    )
    
    return {"message": "Verification email sent. Check your inbox."}


@router.post("/verify-email")
async def verify_email(payload: VerifyEmailRequest):
    """Verify email with token."""
    supabase = get_supabase()
    token = payload.token
    token_hash = hash_token(token)
    
    # Find user with this token
    result = supabase.table("users").select("*").eq("verification_token", token_hash).execute()
    
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid verification token"
        )
    
    user = result.data[0]
    
    # Check if token expired
    expires_at = datetime.fromisoformat(user["verification_token_expires"])
    if datetime.utcnow() > expires_at:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Verification token has expired"
        )
    
    # Mark email as verified
    supabase.table("users").update({
        "email_verified_at": datetime.utcnow().isoformat(),
        "verification_token": None,
        "verification_token_expires": None,
        "updated_at": datetime.utcnow().isoformat(),
    }).eq("id", user["id"]).execute()
    
    return {"message": "Email verified successfully"}


@router.post("/resend-verification-email")
@limiter.limit("3/minute")
async def resend_verification_email(request: Request, user_id: str = Depends(get_current_user)):
    """Resend verification email for unverified users."""
    supabase = get_supabase()
    
    # Get user
    result = supabase.table("users").select("*").eq("id", user_id).execute()
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user = result.data[0]
    
    # Check if already verified
    if user.get("email_verified_at"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already verified"
        )
    
    # Generate new verification token
    token = generate_token(32)
    token_hash = hash_token(token)
    expires_at = (datetime.utcnow() + timedelta(hours=24)).isoformat()
    
    # Update token in database
    supabase.table("users").update({
        "verification_token": token_hash,
        "verification_token_expires": expires_at,
        "updated_at": datetime.utcnow().isoformat(),
    }).eq("id", user_id).execute()
    
    # Send verification email
    settings = get_settings()
    email_service = get_email_service()
    email_service.send_verification_email(
        user["email"],
        user.get("full_name"),
        token,
        frontend_url=settings.frontend_url
    )
    
    return {"message": "Verification email resent. Check your inbox."}


@router.post("/forgot-password")
@limiter.limit("5/minute")
async def forgot_password(request: Request, payload: ForgotPasswordRequest):
    """Request password reset for a user by email."""
    supabase = get_supabase()
    
    # Find user by email
    result = supabase.table("users").select("*").eq("email", payload.email).execute()
    
    if not result.data:
        # Return generic message for security (don't reveal if email exists)
        return {"message": "If email exists, password reset link has been sent"}
    
    user = result.data[0]
    
    # Generate reset token
    token = generate_token(32)
    token_hash = hash_token(token)
    expires_at = (datetime.utcnow() + timedelta(hours=1)).isoformat()
    
    # Store reset token in database
    supabase.table("users").update({
        "password_reset_token": token_hash,
        "password_reset_token_expires": expires_at,
        "updated_at": datetime.utcnow().isoformat(),
    }).eq("id", user["id"]).execute()
    
    # Send reset email
    settings = get_settings()
    email_service = get_email_service()
    email_service.send_password_reset_email(
        user["email"],
        user.get("full_name"),
        token,
        frontend_url=settings.frontend_url
    )
    
    return {"message": "If email exists, password reset link has been sent"}


@router.post("/verify-reset-token")
async def verify_reset_token(payload: VerifyResetTokenRequest):
    """Check if a password reset token is valid."""
    supabase = get_supabase()
    token = payload.token
    token_hash = hash_token(token)
    
    # Find user with this token
    result = supabase.table("users").select("*").eq("password_reset_token", token_hash).execute()
    
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid reset token"
        )
    
    user = result.data[0]
    
    # Check if token expired
    expires_at = datetime.fromisoformat(user["password_reset_token_expires"])
    if datetime.utcnow() > expires_at:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Reset token has expired"
        )
    
    return {"message": "Token is valid"}


@router.post("/reset-password")
@limiter.limit("5/minute")
async def reset_password(request: Request, payload: ResetPasswordRequest):
    """Reset password with a valid token."""
    supabase = get_supabase()
    token = payload.token
    token_hash = hash_token(token)
    
    # Validate new password
    is_valid, error_msg = validate_password(payload.new_password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    
    # Check passwords match
    if payload.new_password != payload.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match"
        )
    
    # Find user with this token
    result = supabase.table("users").select("*").eq("password_reset_token", token_hash).execute()
    
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid reset token"
        )
    
    user = result.data[0]
    
    # Check if token expired
    expires_at = datetime.fromisoformat(user["password_reset_token_expires"])
    if datetime.utcnow() > expires_at:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Reset token has expired"
        )
    
    # Update password and clear reset token
    password_hash = hash_password(payload.new_password)
    supabase.table("users").update({
        "password_hash": password_hash,
        "password_reset_token": None,
        "password_reset_token_expires": None,
        "updated_at": datetime.utcnow().isoformat(),
    }).eq("id", user["id"]).execute()
    
    return {"message": "Password reset successfully"}
