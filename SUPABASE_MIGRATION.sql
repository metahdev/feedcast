-- Migration: Add user profile fields and news sources
-- Run this in Supabase SQL Editor to add new fields to existing database

-- Add new columns to users table
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS country TEXT,
ADD COLUMN IF NOT EXISTS age INTEGER,
ADD COLUMN IF NOT EXISTS gender TEXT,
ADD COLUMN IF NOT EXISTS occupation TEXT,
ADD COLUMN IF NOT EXISTS news_sources TEXT[] DEFAULT '{}';

-- Add comments to document the columns
COMMENT ON COLUMN users.country IS 'User''s country of residence';
COMMENT ON COLUMN users.age IS 'User''s age';
COMMENT ON COLUMN users.gender IS 'User''s gender identity';
COMMENT ON COLUMN users.occupation IS 'User''s occupation or job title';
COMMENT ON COLUMN users.news_sources IS 'Array of news sources the user follows (e.g., BBC, CNN, NYT)';

-- Note: RLS policies remain the same - users can only access their own data
-- No changes needed to existing policies

-- Verify the migration
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'users' 
AND column_name IN ('country', 'age', 'gender', 'occupation', 'news_sources');

