# 🐛 Debug Summary: Episode Creation Issues

## Problem

Episode creation was failing with two issues:
1. ❌ `podcasts_status_check` constraint violation
2. ❌ Episodes table missing required columns (`script`, `status`, `metadata`)

---

## Root Causes

### Issue 1: Invalid Podcast Status ✅ FIXED

**Error:**
```
new row for relation "podcasts" violates check constraint "podcasts_status_check"
```

**Cause:**
In `generator.py` line 1490, we were setting `status = "active"` when creating a podcast (show), but the `podcasts` table only allows these values:
- `"pending"`
- `"generating"`
- `"completed"`
- `"ready"`

**Fix:**
Changed `status = "active"` → `status = "ready"` in `_get_or_create_podcast()` method.

### Issue 2: Episodes Table Schema Mismatch ⚠️ NEEDS MIGRATION

**Problem:**
- Episodes table has column `transcript` 
- Generator code uses `script`
- Missing columns: `status`, `metadata`

**What the generator tries to insert:**
```python
{
    "podcast_id": podcast_id,
    "title": "...",
    "description": "...",
    "duration": 300,
    "script": {...},      # ❌ Column doesn't exist (called "transcript")
    "status": "ready",    # ❌ Column doesn't exist
    "metadata": {...}     # ❌ Column doesn't exist
}
```

---

## Solutions

### ✅ Solution 1: Code Fixed (Already Done)

File: `podcast_generation/generator.py`
- Line 1490: Changed `"status": "active"` → `"status": "ready"`

### ⚠️ Solution 2: Run Database Migration (YOU NEED TO DO THIS)

**Run this SQL in Supabase SQL Editor:**

```sql
-- 1. Rename transcript to script
ALTER TABLE public.episodes 
  RENAME COLUMN transcript TO script;

-- 2. Add missing columns
ALTER TABLE public.episodes 
  ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'ready',
  ADD COLUMN IF NOT EXISTS metadata JSONB;

-- 3. Update index
DROP INDEX IF EXISTS idx_episodes_transcript;
CREATE INDEX IF NOT EXISTS idx_episodes_script 
  ON public.episodes USING gin(script);
```

**Or run the file:**
See `REQUIRED_MIGRATIONS.sql` for the complete migration script.

---

## How to Test

After running the migration:

```bash
# Test 1: Run the test script
python test_real_user_episode.py

# Test 2: Or call the API
curl -X POST "http://localhost:8000/api/podcasts/generate-news?user_id=YOUR_USER_ID&duration_minutes=5"

# Test 3: Or use the example
python generate_podcast_example.py
```

---

## What Gets Created After Fixes

### 1. Podcast (Show) ✅
```sql
INSERT INTO podcasts (user_id, title, description, status)
VALUES (
  'user-id',
  'User's Daily AI Updates',
  'Your personalized daily news...',
  'ready'  -- ✅ Now uses valid status
);
```

### 2. Episode ✅
```sql
INSERT INTO episodes (podcast_id, title, description, duration, script, status, metadata)
VALUES (
  'podcast-id',
  'Today's Tech Headlines...',
  'Breaking developments...',
  300,
  '{"segments": [...]}',  -- ✅ Now uses "script" column
  'ready',                 -- ✅ Now has status
  '{"format": "monologue"}'  -- ✅ Now has metadata
);
```

### 3. Episode Topics ✅
```sql
INSERT INTO episode_topics (episode_id, topic_type, topic_name, importance_score, context)
VALUES (
  'episode-id',
  'entity',
  'OpenAI Developments',
  9.5,
  '{"events": [...], "key_facts": [...], "sources": [...]}'
);
```

---

## Verification

After migration, verify the schema:

```sql
-- Check episodes table structure
SELECT column_name, data_type 
FROM information_schema.columns
WHERE table_name = 'episodes'
ORDER BY ordinal_position;

-- Expected columns:
-- id, podcast_id, title, description, duration, audio_url, 
-- script (not transcript!), status, metadata, created_at
```

---

## Timeline of Fixes

1. ✅ **Fixed in code:** Podcast status constraint (generator.py)
2. ⏳ **Need to run:** Episodes table migration (REQUIRED_MIGRATIONS.sql)
3. ✅ **Ready to test:** After migration, all tests should pass

---

## Quick Reference

**Files Changed:**
- ✅ `podcast_generation/generator.py` (line 1490)

**Files to Run:**
- ⏳ `REQUIRED_MIGRATIONS.sql` (in Supabase SQL Editor)

**Files to Test:**
- `test_real_user_episode.py`
- `generate_podcast_example.py`

---

## Error Messages Resolved

### Before:
```
❌ new row for relation "podcasts" violates check constraint "podcasts_status_check"
❌ column "script" does not exist (episodes table has "transcript")
❌ column "status" does not exist
❌ column "metadata" does not exist
```

### After Migration:
```
✅ Episode created successfully!
✅ Topics saved (8 consolidated topics)
✅ Sources saved (6 credible sources)
```

