-- Migration: Add onboarded column to users table
-- Purpose: Track whether user has completed onboarding process
-- Date: 2025-10-26

-- Add onboarded column to users table (defaults to false for new users)
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS onboarded BOOLEAN DEFAULT FALSE NOT NULL;

-- Optional: If you want to mark existing users as already onboarded
-- Uncomment the following line if needed:
-- UPDATE users SET onboarded = TRUE WHERE created_at < NOW();

-- Verify the column was added
SELECT column_name, data_type, column_default 
FROM information_schema.columns 
WHERE table_name = 'users' AND column_name = 'onboarded';

