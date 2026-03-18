#!/usr/bin/env python3
"""Check if api_keys column exists in user_settings table."""

import sys
sys.path.insert(0, '/Users/nate/Desktop/ai-agent/backend')

from app.memory.supabase_client import get_supabase

try:
    sb = get_supabase()
    result = sb.table("user_settings").select("*").limit(1).execute()
    
    if result.data:
        record = result.data[0]
        print("✓ user_settings table exists")
        print(f"Columns: {list(record.keys())}")
        has_api_keys = 'api_keys' in record
        print(f"api_keys column exists: {has_api_keys}")
    else:
        print("⚠ No records found in user_settings")
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
