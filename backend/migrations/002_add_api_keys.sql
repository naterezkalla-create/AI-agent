-- Migration: Add API Keys Support to User Settings
-- Description: Add JSONB column for storing encrypted API keys per user
-- Created: 2026-03-18

-- Add api_keys column to user_settings table
-- This stores encrypted API keys in JSONB format
-- Example structure: {"anthropic": "encrypted_key_string", "openai": "encrypted_key_string"}
ALTER TABLE user_settings 
ADD COLUMN IF NOT EXISTS api_keys JSONB DEFAULT '{}';

-- Create an index on the column for better query performance
CREATE INDEX IF NOT EXISTS idx_user_settings_api_keys ON user_settings USING GIN (api_keys);

-- Verify the column was added
SELECT column_name, data_type FROM information_schema.columns 
WHERE table_name = 'user_settings' AND column_name = 'api_keys';
