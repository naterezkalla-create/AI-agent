#!/usr/bin/env python3
"""Create a test user in the database."""

import sys
import os
sys.path.insert(0, '/Users/nate/Desktop/ai-agent/backend')

from app.core.auth import hash_password, create_access_token
from app.memory.supabase_client import get_supabase
from datetime import datetime
import uuid

# Create user
supabase = get_supabase()
user_id = str(uuid.uuid4())

user_data = {
    "id": user_id,
    "email": "naterezkalla@gmail.com",
    "password_hash": hash_password("Converse14"),
    "full_name": "Nate",
    "is_active": True,
    "email_verified": False,
    "created_at": datetime.utcnow().isoformat(),
    "updated_at": datetime.utcnow().isoformat(),
}

# Insert user
user_response = supabase.table("users").insert(user_data).execute()

if user_response.data:
    print("✅ User created successfully!")
    print(f"User ID: {user_id}")
    print(f"Email: naterezkalla@gmail.com")
    print(f"Name: Nate")
    
    # Create default user settings
    supabase.table("user_settings").insert({
        "user_id_fk": user_id,
        "system_prompt": "",
        "enabled_integrations": {},
        "preferences": {},
        "api_keys": {},
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }).execute()
    
    print("✅ User settings created!")
    
    # Generate token
    token = create_access_token(user_id)
    print(f"\n🔑 Access Token:\n{token}")
    print("\nYou can now log in with:")
    print("  Email: naterezkalla@gmail.com")
    print("  Password: Converse14")
else:
    print("❌ Failed to create user")
    print(user_response)
