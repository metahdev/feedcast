-- Migration: Add transcript column to episodes table
-- This is optional - transcripts are stored in memory for now
-- Run this in Supabase SQL Editor if you want to store transcripts in the database

-- Add transcript column to episodes table
ALTER TABLE episodes 
ADD COLUMN IF NOT EXISTS transcript JSONB;

-- Add comment to document the column
COMMENT ON COLUMN episodes.transcript IS 'JSON array of timestamped transcript segments for synchronized playback';

-- Create an index for better query performance if searching transcripts
CREATE INDEX IF NOT EXISTS idx_episodes_transcript 
ON episodes USING GIN (transcript);

-- Verify the migration
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'episodes' 
AND column_name = 'transcript';

-- Example transcript structure:
-- [
--   {
--     "text": "Welcome to the podcast...",
--     "startTime": 0.0,
--     "endTime": 3.5
--   },
--   {
--     "text": "Today we're discussing...",
--     "startTime": 3.5,
--     "endTime": 7.2
--   }
-- ]

