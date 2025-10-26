# 🎙️ How to Generate a Personalized News Podcast

## Quick Start

### Prerequisites
1. User must exist in `users` table
2. User must have interests in `user_interests` table

---

## API Endpoint

```
POST /api/podcasts/generate-news
```

### Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `user_id` | string (UUID) | ✅ Yes | - | User's UUID from `users` table |
| `duration_minutes` | integer | No | 5 | Podcast duration (1-30 minutes) |

### Response

Returns immediately while generation happens in background:

```json
{
  "podcast_id": "generating-<user_id>",
  "status": "generating",
  "estimated_completion_time": "2025-10-26T12:34:56Z",
  "message": "Episode generation started! Based on 3 interests: AI, technology, science. Check back in ~3 minutes."
}
```

---

## 📱 Usage Examples

### 1. cURL (Terminal)

```bash
# Generate 5-minute podcast for user
curl -X POST "http://localhost:8000/api/podcasts/generate-news?user_id=0ab3d613-b53b-41f0-9442-47c9e05cf636&duration_minutes=5"

# Generate 10-minute podcast
curl -X POST "http://localhost:8000/api/podcasts/generate-news?user_id=0ab3d613-b53b-41f0-9442-47c9e05cf636&duration_minutes=10"
```

### 2. Python (Requests)

```python
import requests
import time

# User ID
user_id = "0ab3d613-b53b-41f0-9442-47c9e05cf636"

# Generate podcast
response = requests.post(
    "http://localhost:8000/api/podcasts/generate-news",
    params={
        "user_id": user_id,
        "duration_minutes": 5
    }
)

result = response.json()
print(f"Status: {result['status']}")
print(f"Message: {result['message']}")
print(f"Wait ~3 minutes for completion...")

# Wait for completion (3-4 minutes)
time.sleep(180)

# Check episodes table for result
```

### 3. JavaScript/TypeScript (Fetch)

```typescript
async function generatePodcast(userId: string, durationMinutes: number = 5) {
  const response = await fetch(
    `http://localhost:8000/api/podcasts/generate-news?user_id=${userId}&duration_minutes=${durationMinutes}`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      }
    }
  );
  
  const result = await response.json();
  console.log('Generation started:', result);
  
  return result;
}

// Usage
const userId = "0ab3d613-b53b-41f0-9442-47c9e05cf636";
generatePodcast(userId, 5)
  .then(result => {
    console.log(`Podcast generating! Check back in ~3 minutes`);
    console.log(`Message: ${result.message}`);
  });
```

### 4. React Hook Example

```typescript
import { useState } from 'react';

function usePodcastGeneration() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  
  const generatePodcast = async (userId: string, duration: number = 5) => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(
        `http://localhost:8000/api/podcasts/generate-news?user_id=${userId}&duration_minutes=${duration}`,
        { method: 'POST' }
      );
      
      if (!response.ok) {
        throw new Error('Failed to start generation');
      }
      
      const data = await response.json();
      setResult(data);
      return data;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  };
  
  return { generatePodcast, loading, result, error };
}

// Usage in component
function PodcastGenerator({ userId }) {
  const { generatePodcast, loading, result } = usePodcastGeneration();
  
  const handleGenerate = async () => {
    try {
      const result = await generatePodcast(userId, 5);
      console.log('Started:', result);
      // Show notification: "Podcast generating! Check back in 3 minutes"
    } catch (error) {
      console.error('Failed:', error);
    }
  };
  
  return (
    <button onClick={handleGenerate} disabled={loading}>
      {loading ? 'Starting...' : 'Generate Podcast'}
    </button>
  );
}
```

### 5. Swift/iOS Example

```swift
func generatePodcast(userId: String, duration: Int = 5) async throws {
    guard let url = URL(string: "http://localhost:8000/api/podcasts/generate-news?user_id=\(userId)&duration_minutes=\(duration)") else {
        throw URLError(.badURL)
    }
    
    var request = URLRequest(url: url)
    request.httpMethod = "POST"
    
    let (data, response) = try await URLSession.shared.data(for: request)
    
    guard let httpResponse = response as? HTTPURLResponse,
          httpResponse.statusCode == 200 else {
        throw URLError(.badServerResponse)
    }
    
    let result = try JSONDecoder().decode(PodcastGenerationResponse.self, from: data)
    print("Generation started: \(result.message)")
}

struct PodcastGenerationResponse: Codable {
    let podcast_id: String
    let status: String
    let message: String
}
```

---

## 🔄 Complete Workflow

### Step 1: Ensure User Has Interests

Before generating, make sure user has interests:

```sql
-- Check if user has interests
SELECT * FROM user_interests WHERE user_id = '0ab3d613-b53b-41f0-9442-47c9e05cf636';

-- If not, add some interests
INSERT INTO user_interests (user_id, interest, weight) VALUES
  ('0ab3d613-b53b-41f0-9442-47c9e05cf636', 'artificial intelligence', 10),
  ('0ab3d613-b53b-41f0-9442-47c9e05cf636', 'technology', 8),
  ('0ab3d613-b53b-41f0-9442-47c9e05cf636', 'science', 6);
```

### Step 2: Call the API

```bash
curl -X POST "http://localhost:8000/api/podcasts/generate-news?user_id=0ab3d613-b53b-41f0-9442-47c9e05cf636&duration_minutes=5"
```

**Response:**
```json
{
  "podcast_id": "generating-0ab3d613-b53b-41f0-9442-47c9e05cf636",
  "status": "generating",
  "message": "Episode generation started! Based on 3 interests: artificial intelligence, technology, science. Check back in ~3 minutes."
}
```

### Step 3: Wait for Completion

Generation takes **2-4 minutes** because it:
- 🔍 Discovers actual news events (not just summaries)
- 📰 Searches multiple sources in parallel
- ✅ Verifies events with fact-checking
- 🎙️ Generates news-style script
- 💾 Saves to database with topics

### Step 4: Check Results

After 3-4 minutes, query the database:

```sql
-- Get the latest episode for user
SELECT e.*, p.title as podcast_title
FROM episodes e
JOIN podcasts p ON e.podcast_id = p.id
WHERE p.user_id = '0ab3d613-b53b-41f0-9442-47c9e05cf636'
ORDER BY e.created_at DESC
LIMIT 1;

-- Get topics for follow-up questions
SELECT topic_type, topic_name, importance_score, context
FROM episode_topics
WHERE episode_id = '<episode_id_from_above>'
ORDER BY importance_score DESC;

-- Get sources used
SELECT title, publication, url
FROM sources
WHERE episode_id = '<episode_id>';
```

---

## 📊 What Gets Created

When you call this endpoint, it creates:

### 1. Podcast (Show) - if doesn't exist
```
Title: "Tim's Daily AI Updates"
Description: "Personalized daily news on artificial intelligence, technology, science"
User ID: <user_id>
```

### 2. Episode (Broadcast)
```
Title: "Today's Tech Headlines: October 26, 2025"
Description: "Breaking developments in AI, technology breakthroughs, and science news"
Duration: 300 seconds (5 minutes)
Script: { segments: [...] }  // Full SSML script
Status: "ready"
Podcast ID: <podcast_id>
```

### 3. Episode Topics (for follow-ups)
```
- "OpenAI Developments" (entity, importance: 9.5)
- "AI Policy & Regulation" (theme, importance: 8.0)
- "Healthcare AI" (theme, importance: 7.5)
```

### 4. Sources & Fact Checks
```
- 6-8 credible sources from multiple publications
- Fact checks for key claims
```

---

## ⚠️ Requirements & Errors

### Requirements
- ✅ User must exist in `users` table
- ✅ User must have at least 1 interest in `user_interests` table
- ✅ Backend must be running (`uvicorn main:app --reload`)
- ✅ Environment variables set (ANTHROPIC_API_KEY, SUPABASE_URL, etc.)

### Common Errors

**404 - User not found**
```json
{
  "detail": "User not found"
}
```
→ Check user_id exists in `users` table

**400 - No interests found**
```json
{
  "detail": "No interests found for user. Please add interests first via POST /users/{user_id}/interests"
}
```
→ Add interests to `user_interests` table

**500 - Generation failed**
```json
{
  "detail": "Podcast generation failed: <error>"
}
```
→ Check logs for details, verify API keys

---

## 🎯 Testing Script

Here's a complete test script:

```python
import requests
import time
from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

# Setup
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Get a user
users = supabase.table("users").select("id, email").limit(1).execute()
user_id = users.data[0]["id"]
print(f"Using user: {user_id}")

# Check/add interests
interests = supabase.table("user_interests").select("*").eq("user_id", user_id).execute()
if not interests.data:
    print("Adding interests...")
    supabase.table("user_interests").insert([
        {"user_id": user_id, "interest": "artificial intelligence", "weight": 10},
        {"user_id": user_id, "interest": "technology", "weight": 8},
    ]).execute()

# Generate podcast
print("Generating podcast...")
response = requests.post(
    "http://localhost:8000/api/podcasts/generate-news",
    params={"user_id": user_id, "duration_minutes": 5}
)
result = response.json()
print(f"Status: {result['status']}")
print(f"Message: {result['message']}")

# Wait for completion
print("Waiting 3 minutes for completion...")
time.sleep(180)

# Check result
episodes = supabase.table("episodes").select("*").order("created_at", desc=True).limit(1).execute()
if episodes.data:
    episode = episodes.data[0]
    print(f"\n✅ Episode created!")
    print(f"Title: {episode['title']}")
    print(f"Duration: {episode['duration']}s")
    
    # Get topics
    topics = supabase.table("episode_topics").select("*").eq("episode_id", episode["id"]).execute()
    print(f"\nTopics ({len(topics.data)}):")
    for topic in topics.data[:5]:
        print(f"  - {topic['topic_name']} (score: {topic['importance_score']})")
else:
    print("❌ No episode created yet - may need more time")
```

---

## 🚀 Production Deployment

For production, add:

1. **Webhook for completion notification:**
```python
# In background task, after generation:
requests.post(
    f"https://your-app.com/api/webhooks/podcast-complete",
    json={"episode_id": episode_id, "user_id": user_id}
)
```

2. **Polling endpoint to check status:**
```python
@router.get("/api/podcasts/status/{user_id}")
async def check_generation_status(user_id: str):
    # Check for recent episodes
    pass
```

3. **Email notification when complete:**
```python
# Send email with link to new episode
```

---

## 📖 Related Documentation

- `API_USAGE_NEWS_PODCAST.md` - Detailed API documentation
- `REFACTORING_PODCASTS_TO_EPISODES.md` - Database schema
- `generator.py` - Core generation logic

---

## 💡 Tips

1. **Duration:** Start with 5 minutes for testing, increase to 10-15 for production
2. **Caching:** Subsequent generations on same topics are faster due to caching
3. **Topics:** More specific interests = better quality episodes
4. **Follow-ups:** Use `episode_topics` to answer user questions about the episode

