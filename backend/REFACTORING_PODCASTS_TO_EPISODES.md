# 🔄 Refactoring: Podcasts → Episodes Schema

## Changes Made

Refactored the system to properly separate **Podcasts** (the show) from **Episodes** (individual chapters).

---

## Schema Change

### Before (Incorrect):
```
podcasts table = Individual podcast episodes
podcast_topics table = Topics for each podcast
```

❌ **Problem**: Each generated "podcast" was standalone, no concept of a show

### After (Correct):
```
podcasts table = The show itself (e.g., "Tim's Daily AI Updates")
episodes table = Individual episodes under the podcast
episode_topics table = Topics for each episode
```

✅ **Solution**: Podcast = Book, Episode = Chapter

---

## Database Schema

### `podcasts` Table (The Show)
```sql
CREATE TABLE podcasts (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  title TEXT,              -- "Tim's Daily AI Updates"
  description TEXT,        -- "Your personalized daily news"
  status TEXT,             -- "active", "archived"
  created_at TIMESTAMPTZ
);
```

### `episodes` Table (Individual Chapters)
```sql
CREATE TABLE episodes (
  id UUID PRIMARY KEY,
  podcast_id UUID REFERENCES podcasts(id),  -- Parent podcast
  user_id UUID REFERENCES users(id),
  title TEXT,                                -- "October 26, 2025 - AI News"
  description TEXT,
  duration INTEGER,                          -- Duration in seconds
  script JSONB,                              -- Full script
  status TEXT,                               -- "ready", "generating", "failed"
  metadata JSONB,
  created_at TIMESTAMPTZ
);
```

### `episode_topics` Table (Topics per Episode)
```sql
CREATE TABLE episode_topics (
  id UUID PRIMARY KEY,
  episode_id UUID REFERENCES episodes(id),   -- Which episode
  podcast_id UUID REFERENCES podcasts(id),   -- Which show
  user_id UUID REFERENCES users(id),
  topic_type TEXT,                           -- "entity", "theme"
  topic_name TEXT,                           -- "OpenAI Developments"
  summary TEXT,
  key_facts JSONB,
  entities_mentioned JSONB,
  source_urls JSONB,
  segment_mentioned TEXT,
  importance_score FLOAT,
  created_at TIMESTAMPTZ
);
```

### `sources` Table
```sql
-- Now linked to episode_id instead of podcast_id
ALTER TABLE sources 
  DROP COLUMN podcast_id,
  ADD COLUMN episode_id UUID REFERENCES episodes(id);
```

### `fact_checks` Table
```sql
-- Now linked to episode_id instead of podcast_id
ALTER TABLE fact_checks
  DROP COLUMN podcast_id,
  ADD COLUMN episode_id UUID REFERENCES episodes(id);
```

---

## Code Changes

### 1. `generator.py`

**New Method:**
```python
async def _get_or_create_podcast(user_id, podcast_data) -> str:
    """
    Get or create the user's main Podcast (the show).
    Returns podcast_id.
    """
    # Check if user already has a podcast
    # If yes: return existing podcast_id
    # If no: create new podcast with title like "Tim's Daily AI Updates"
```

**Updated Method:**
```python
async def save_to_database(podcast_data) -> str:
    """
    Now returns episode_id instead of podcast_id.
    
    Flow:
    1. Get or create Podcast (the show)
    2. Create Episode under that podcast
    3. Save sources (linked to episode)
    4. Save fact_checks (linked to episode)
    5. Save episode_topics (linked to episode AND podcast)
    """
```

**Renamed Method:**
```python
# Before:
async def _save_podcast_topics(podcast_id, user_id, events, script)

# After:
async def _save_episode_topics(episode_id, podcast_id, user_id, events, script)
```

### 2. `podcast_router.py`

**Updated Endpoint:**
```python
@router.post("/podcasts/generate-news")
async def generate_personalized_news_podcast(...):
    """
    Now generates EPISODES under the user's podcast.
    
    Returns:
    - podcast_id: "generating-{user_id}" (temp ID)
    - The actual episode_id is created by the generator
    """
```

**Updated Background Task:**
```python
async def generate_news_podcast_background(generator, request, user_id, top_interests):
    """
    Generates episode (not standalone podcast).
    Episode is automatically added to user's podcast (show).
    """
```

---

## How It Works Now

### First Episode Generation:
```
User calls: POST /podcasts/generate-news?user_id=123

1. Generator runs
2. No podcast exists for user
3. CREATE Podcast: "Tim's Daily AI Updates"
4. CREATE Episode: "October 26 - AI News" (under that podcast)
5. SAVE episode_topics: 4-5 consolidated topics
```

### Subsequent Episode Generations:
```
User calls: POST /podcasts/generate-news?user_id=123

1. Generator runs
2. Podcast already exists for user
3. USE existing Podcast: "Tim's Daily AI Updates"
4. CREATE Episode: "October 27 - AI News" (under same podcast)
5. SAVE episode_topics: 4-5 consolidated topics
```

---

## User Experience

### Before:
```
GET /podcasts?user_id=123

Response:
- "AI News Podcast 1"
- "AI News Podcast 2"
- "AI News Podcast 3"

❌ Each is standalone, no organization
```

### After:
```
GET /podcasts?user_id=123

Response:
- "Tim's Daily AI Updates"
  ├── Episode 1: "October 26 - AI News"
  ├── Episode 2: "October 27 - Tech Roundup"
  └── Episode 3: "October 28 - Policy Update"

✅ Organized by show, episodes are chapters
```

---

## API Changes

### Endpoint (No Change):
```
POST /api/podcasts/generate-news?user_id={uuid}&duration_minutes=5
```

### Response (No Breaking Changes):
```json
{
  "podcast_id": "generating-123",  // Temp ID during generation
  "status": "generating",
  "estimated_completion_time": "2025-10-26T18:45:00Z",
  "message": "Generating personalized news episode..."
}
```

### What Gets Created:
```
Podcast (if first time):
  id: abc-123
  title: "Tim's Daily AI Updates"
  
Episode:
  id: xyz-789
  podcast_id: abc-123
  title: "October 26, 2025 - AI News"
  
Episode Topics (4-5 topics):
  - OpenAI Developments
  - White House Policy
  - AI in Healthcare
  - AI Safety & Security
```

---

## Benefits

### 1. **Proper Organization**
- Podcast = The show
- Episodes = Individual chapters
- Users see their content organized properly

### 2. **Better History**
- "Show me all episodes of my AI podcast"
- "Show me yesterday's episode"
- Chronological organization

### 3. **Follow-up Context**
- Topics are per-episode
- Can ask: "Tell me more about that OpenAI story from yesterday's episode"
- Links to specific episode

### 4. **Scalability**
- One podcast per user (or per topic category)
- Unlimited episodes under each podcast
- Better database structure

---

## Migration Required

If you have existing data in `podcasts` table, you need to:

1. **Create podcasts for existing users**
```sql
-- Create one podcast per user
INSERT INTO podcasts (user_id, title, description, status)
SELECT DISTINCT 
  user_id,
  user_id || '''s Daily News',
  'Your personalized daily news',
  'active'
FROM podcasts_old;
```

2. **Migrate old podcasts to episodes**
```sql
-- Convert old podcasts to episodes
INSERT INTO episodes (podcast_id, user_id, title, description, duration, script, status, created_at)
SELECT 
  p.id AS podcast_id,
  po.user_id,
  po.title,
  po.description,
  po.total_duration * 60 AS duration,
  po.script,
  po.status,
  po.created_at
FROM podcasts_old po
JOIN podcasts p ON p.user_id = po.user_id;
```

3. **Update sources and fact_checks**
```sql
-- Update sources to point to episodes
ALTER TABLE sources ADD COLUMN episode_id UUID;
UPDATE sources s
SET episode_id = (
  SELECT e.id FROM episodes e 
  WHERE e.old_podcast_id = s.podcast_id
);
ALTER TABLE sources DROP COLUMN podcast_id;
```

4. **Rename podcast_topics to episode_topics**
```sql
ALTER TABLE podcast_topics RENAME TO episode_topics;
ALTER TABLE episode_topics ADD COLUMN episode_id UUID;
-- Migrate data...
```

---

## Testing

```bash
# Test the refactored system
cd /Users/Tim/Desktop/Berkeley/hackathon/feedcast/backend
python test_full_end_to_end.py
```

**Expected Results:**
- ✅ Podcast created (or existing one used)
- ✅ Episode created under that podcast
- ✅ 4-5 topics saved to episode_topics
- ✅ No duplicate podcasts for same user

---

## Status

✅ **Code Refactored**  
⏳ **Database Schema** - Needs migration  
⏳ **Frontend** - Needs update to display podcasts/episodes properly  

---

**Refactored Date:** October 26, 2025  
**Files Modified:** `generator.py`, `podcast_router.py`  
**Tables Affected:** `podcasts`, `episodes`, `episode_topics`, `sources`, `fact_checks`

