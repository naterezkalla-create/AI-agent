-- Migration: Add Email Verification and Password Reset Support
-- Description: Add columns for email verification tokens and password reset flows
-- Created: 2026-03-18

-- Add columns for email verification and password reset
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS email_verified_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS verification_token VARCHAR(255),
ADD COLUMN IF NOT EXISTS verification_token_expires TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS password_reset_token VARCHAR(255),
ADD COLUMN IF NOT EXISTS password_reset_token_expires TIMESTAMP WITH TIME ZONE;

-- Create indexes for token lookups
CREATE INDEX IF NOT EXISTS idx_users_verification_token ON users(verification_token);
CREATE INDEX IF NOT EXISTS idx_users_password_reset_token ON users(password_reset_token);

-- Verify columns were added
SELECT column_name FROM information_schema.columns 
WHERE table_name = 'users' AND column_name IN ('verification_token', 'password_reset_token')
ORDER BY column_name;
