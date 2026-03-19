from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from app.memory.supabase_client import get_supabase
from app.core.encryption import encrypt_api_key, decrypt_api_key
from typing import Optional, List, Dict
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/settings", tags=["settings"])


class UserSettings(BaseModel):
    system_prompt: Optional[str] = None
    enabled_integrations: Optional[List[str]] = None
    preferences: Optional[dict] = None


class SettingsResponse(BaseModel):
    id: str
    user_id: str
    system_prompt: str
    enabled_integrations: List[str]
    preferences: dict
    created_at: str
    updated_at: str


class APIKeyRequest(BaseModel):
    key: str  # The actual API key to store


class APIKeyResponse(BaseModel):
    service: str
    has_key: bool  # Never return the actual key


class APIKeysListResponse(BaseModel):
    keys: Dict[str, bool]  # service -> has_key mapping


@router.get("/", response_model=SettingsResponse)
async def get_settings(user_id: str = Query("default")):
    """Get user settings"""
    try:
        sb = get_supabase()
        result = sb.table("user_settings").select("*").eq("user_id", user_id).execute()
        
        if not result.data:
            # Create default settings if they don't exist
            default_settings = await create_default_settings(user_id, sb)
            return default_settings
        
        return result.data[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def create_default_settings(user_id: str, sb=None):
    """Create default settings for a new user"""
    if sb is None:
        sb = get_supabase()
    
    default_data = {
        "user_id": user_id,
        "system_prompt": "You are a helpful AI assistant. Be concise and professional.",
        "enabled_integrations": ["google", "telegram"],
        "preferences": {
            "timezone": "Australia/Sydney",
            "theme": "dark",
            "notifications_enabled": True,
            "auto_save_conversations": True,
        },
        "api_keys": {},  # Empty JSONB object for encrypted API keys
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }
    
    result = sb.table("user_settings").insert(default_data).execute()
    return result.data[0] if result.data else default_data


@router.put("/", response_model=SettingsResponse)
async def update_settings(settings: UserSettings, user_id: str = Query("default")):
    """Update user settings"""
    try:
        sb = get_supabase()
        
        # Prepare update data
        update_data = {
            "updated_at": datetime.utcnow().isoformat(),
        }
        
        if settings.system_prompt is not None:
            update_data["system_prompt"] = settings.system_prompt
        if settings.enabled_integrations is not None:
            update_data["enabled_integrations"] = settings.enabled_integrations
        if settings.preferences is not None:
            # Merge with existing preferences
            existing = sb.table("user_settings").select("preferences").eq("user_id", user_id).execute()
            if existing.data and existing.data[0].get("preferences"):
                merged_prefs = {**existing.data[0]["preferences"], **settings.preferences}
                update_data["preferences"] = merged_prefs
            else:
                update_data["preferences"] = settings.preferences
        
        result = sb.table("user_settings").update(update_data).eq("user_id", user_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Settings not found")
        
        logger.info(f"Settings updated for user: {user_id}")
        return result.data[0]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update settings: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reset", response_model=SettingsResponse)
async def reset_settings(user_id: str = Query("default")):
    """Reset settings to defaults"""
    try:
        sb = get_supabase()
        
        # Delete existing settings
        sb.table("user_settings").delete().eq("user_id", user_id).execute()
        
        # Create new default settings
        return await create_default_settings(user_id, sb)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/integrations/{integration}/toggle")
async def toggle_integration(integration: str, enabled: bool = Query(...), user_id: str = Query("default")):
    """Enable/disable a specific integration"""
    try:
        sb = get_supabase()
        result = sb.table("user_settings").select("enabled_integrations").eq("user_id", user_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Settings not found")
        
        integrations = result.data[0].get("enabled_integrations", [])
        
        if enabled and integration not in integrations:
            integrations.append(integration)
        elif not enabled and integration in integrations:
            integrations.remove(integration)
        
        update_result = sb.table("user_settings").update({
            "enabled_integrations": integrations,
            "updated_at": datetime.utcnow().isoformat(),
        }).eq("user_id", user_id).execute()
        
        return {"success": True, "integration": integration, "enabled": enabled, "integrations": integrations}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# API Key Management Endpoints

@router.get("/keys", response_model=APIKeysListResponse)
async def list_api_keys(user_id: str = Query("default")):
    """List which services have API keys configured (never return actual keys)"""
    try:
        sb = get_supabase()
        result = sb.table("user_settings").select("api_keys").eq("user_id", user_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Settings not found")
        
        api_keys_data = result.data[0].get("api_keys", {})
        # Convert to list of services that have keys (without revealing values)
        keys_info = {service: bool(encrypted_key) for service, encrypted_key in api_keys_data.items()}
        
        return {"keys": keys_info}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list API keys: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/keys/{service}", response_model=APIKeyResponse)
async def store_api_key(service: str, request: APIKeyRequest, user_id: str = Query("default")):
    """Store an encrypted API key for a service"""
    try:
        # Validate service name - support many services
        valid_services = [
            # LLM Providers
            "anthropic", "openai", "together_ai_token", "cohere_token",
            # AI/ML Platforms
            "huggingface_token", "replicate_token",
            # Cloud Providers
            "aws_key", "gcp_key", "azure_key",
            # Developer Tools
            "github_token", "google_token", "databricks_token",
            # Communication
            "slack_token", "discord_token", "twilio_key", "sendgrid_key",
            # Financial
            "stripe_key",
            # Generic
            "custom_api_key"
        ]
        
        if service not in valid_services:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid service. Must be one of: {', '.join(valid_services)}"
            )
        
        # Validate key format (basic check)
        if not request.key or len(request.key.strip()) < 10:
            raise HTTPException(status_code=400, detail="API key is invalid or too short")
        
        # Encrypt the API key
        encrypted_key = encrypt_api_key(request.key)
        
        # Get current settings
        sb = get_supabase()
        result = sb.table("user_settings").select("api_keys").eq("user_id", user_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Settings not found")
        
        # Update api_keys JSONB
        api_keys = result.data[0].get("api_keys", {})
        api_keys[service] = encrypted_key
        
        update_result = sb.table("user_settings").update({
            "api_keys": api_keys,
            "updated_at": datetime.utcnow().isoformat(),
        }).eq("user_id", user_id).execute()
        
        if not update_result.data:
            raise HTTPException(status_code=500, detail="Failed to store API key")
        
        logger.info(f"Stored encrypted API key for service: {service}, user: {user_id}")
        
        return {"service": service, "has_key": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to store API key: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/keys/{service}")
async def delete_api_key(service: str, user_id: str = Query("default")):
    """Delete an API key for a service"""
    try:
        sb = get_supabase()
        result = sb.table("user_settings").select("api_keys").eq("user_id", user_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Settings not found")
        
        api_keys = result.data[0].get("api_keys", {})
        
        if service not in api_keys:
            raise HTTPException(status_code=404, detail=f"No API key found for service: {service}")
        
        # Remove the key
        del api_keys[service]
        
        update_result = sb.table("user_settings").update({
            "api_keys": api_keys,
            "updated_at": datetime.utcnow().isoformat(),
        }).eq("user_id", user_id).execute()
        
        logger.info(f"Deleted API key for service: {service}, user: {user_id}")
        
        return {"success": True, "service": service, "message": f"API key for {service} has been deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete API key: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
