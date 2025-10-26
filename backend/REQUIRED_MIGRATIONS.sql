-- ============================================================================
-- REQUIRED DATABASE MIGRATIONS
-- Run these in Supabase SQL Editor to fix episode creation
-- ============================================================================

-- 1. Rename transcript to script (generator uses "script")
ALTER TABLE public.episodes 
  RENAME COLUMN transcript TO script;

-- 2. Add missing columns that generator needs
ALTER TABLE public.episodes 
  ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'ready',
  ADD COLUMN IF NOT EXISTS metadata JSONB;

-- 3. Update index (since we renamed the column)
DROP INDEX IF EXISTS idx_episodes_transcript;
CREATE INDEX IF NOT EXISTS idx_episodes_script 
  ON public.episodes USING gin(script);

-- 4. Verify the changes
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'episodes'
ORDER BY ordinal_position;

-- ============================================================================
-- EXPECTED COLUMNS AFTER MIGRATION:
-- ============================================================================
-- id              | uuid      | NO
-- podcast_id      | uuid      | YES (FK to podcasts)
-- title           | text      | NO
-- description     | text      | YES
-- duration        | real      | NO
-- audio_url       | text      | YES
-- script          | jsonb     | YES  (renamed from transcript)
-- status          | text      | YES  (newly added)
-- metadata        | jsonb     | YES  (newly added)
-- created_at      | timestamp | YES
-- ============================================================================

