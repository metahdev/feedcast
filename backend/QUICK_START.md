# 🚀 Quick Start: Generate a Podcast

## TL;DR - 3 Steps

### 1. Make sure your server is running
```bash
cd /Users/Tim/Desktop/Berkeley/hackathon/feedcast/backend
uvicorn main:app --reload
```

### 2. Call the API
```bash
# Replace with your user_id
curl -X POST "http://localhost:8000/api/podcasts/generate-news?user_id=YOUR_USER_ID&duration_minutes=5"
```

### 3. Wait ~3 minutes, then check the database
```sql
SELECT * FROM episodes ORDER BY created_at DESC LIMIT 1;
```

---

## Even Easier: Use the Test Script

```bash
python generate_podcast_example.py
```

This script will:
- ✅ Find a user from your database
- ✅ Check/add interests if needed
- ✅ Call the API to generate podcast
- ✅ Wait for completion
- ✅ Show you the results

---

## What You Need

1. **User in database** - Must exist in `users` table
2. **User interests** - At least 1 interest in `user_interests` table
3. **API running** - FastAPI server must be running

---

## API Call Details

**Endpoint:** `POST /api/podcasts/generate-news`

**Parameters:**
- `user_id` (required) - User's UUID
- `duration_minutes` (optional) - 5 to 30 minutes (default: 5)

**Example:**
```bash
curl -X POST "http://localhost:8000/api/podcasts/generate-news?user_id=0ab3d613-b53b-41f0-9442-47c9e05cf636&duration_minutes=5"
```

**Response:**
```json
{
  "podcast_id": "generating-0ab3d613-b53b-41f0-9442-47c9e05cf636",
  "status": "generating",
  "message": "Episode generation started! Based on 3 interests..."
}
```

---

## What Gets Created

✅ **Podcast (Show)** - Created once per user
- Title: "Tim's Daily AI Updates"

✅ **Episode** - Each generation creates a new episode
- Title: "Today's Tech Headlines: Oct 26, 2025"
- Script with SSML markup
- 5 minutes of content

✅ **Episode Topics** - For follow-up questions
- "OpenAI Developments"
- "AI Policy & Regulation"
- etc.

✅ **Sources & Fact Checks**
- 6-8 credible sources
- Verified claims

---

## Complete Example (Python)

```python
import requests

user_id = "0ab3d613-b53b-41f0-9442-47c9e05cf636"

# Generate podcast
response = requests.post(
    "http://localhost:8000/api/podcasts/generate-news",
    params={
        "user_id": user_id,
        "duration_minutes": 5
    }
)

print(response.json())
# {'status': 'generating', 'message': '...'}

# Wait ~3 minutes for completion
# Then check episodes table
```

---

## Complete Example (JavaScript/React)

```typescript
async function generatePodcast(userId: string) {
  const response = await fetch(
    `http://localhost:8000/api/podcasts/generate-news?user_id=${userId}&duration_minutes=5`,
    { method: 'POST' }
  );
  
  const result = await response.json();
  console.log(result);
  // {'status': 'generating', 'message': '...'}
  
  // Poll or wait for completion
}
```

---

## Troubleshooting

**❌ "User not found"**
→ User doesn't exist in `users` table

**❌ "No interests found"**
→ Add interests to `user_interests` table:
```sql
INSERT INTO user_interests (user_id, interest, weight) VALUES
  ('your-user-id', 'artificial intelligence', 10);
```

**❌ "Connection refused"**
→ Start your FastAPI server:
```bash
uvicorn main:app --reload
```

**❌ Episode not created after 3 minutes**
→ Check FastAPI logs for errors

---

## Next Steps

📖 See `HOW_TO_GENERATE_PODCAST.md` for complete documentation
🧪 Run `python generate_podcast_example.py` for a full test
🗄️ See `REFACTORING_PODCASTS_TO_EPISODES.md` for database schema

