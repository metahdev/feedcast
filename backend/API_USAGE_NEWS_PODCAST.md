# 📻 Personalized News Podcast API

## Endpoint: Generate News Podcast

**POST** `/api/podcasts/generate-news`

Generates a personalized AI news podcast based on user interests and persona.

---

## Features

✅ **Automatic Interest Detection** - Pulls from `user_interests` table  
✅ **Persona Integration** - Uses user occupation and preferences  
✅ **Event Discovery** - Real news events, not article summaries  
✅ **News-Style Script** - Professional news coverage (no "According to...")  
✅ **Topic Extraction** - Saves to `podcast_topics` for follow-up queries  
✅ **Background Processing** - Returns immediately, generates in background  

---

## Request

### Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `user_id` | string (UUID) | ✅ Yes | - | User ID to generate podcast for |
| `duration_minutes` | integer | No | 5 | Podcast duration (1-30 minutes) |

### Example Request

```bash
curl -X POST "http://localhost:8000/api/podcasts/generate-news?user_id=0ab3d613-b53b-41f0-9442-47c9e05cf636&duration_minutes=5"
```

---

## Response

### Success Response (202 Accepted)

```json
{
  "podcast_id": "0cafc9bc-aa35-4812-a441-9eed24c61641",
  "status": "generating",
  "estimated_completion_time": "2025-10-26T18:45:00Z",
  "message": "Generating personalized news podcast covering: artificial intelligence, machine learning, technology"
}
```

### Error Responses

**404 Not Found** - User doesn't exist
```json
{
  "detail": "User not found"
}
```

**400 Bad Request** - No interests found
```json
{
  "detail": "No interests found for user. Please add interests first via POST /users/{user_id}/interests"
}
```

**500 Internal Server Error** - Generation failed
```json
{
  "detail": "Failed to start podcast generation: [error message]"
}
```

---

## How It Works

### 1. **Fetches User Data**
```sql
-- Gets user persona
SELECT * FROM users WHERE id = ?

-- Gets user interests
SELECT interest, weight FROM user_interests 
WHERE user_id = ? 
ORDER BY weight DESC
```

### 2. **Selects Top Interests**
Takes top 5 interests by weight:
- Interest 1 (highest weight) → Used in INTRO
- Interests 1-5 → Used in main NEWS_OF_DAY segment

### 3. **Generates News Podcast**
- Uses **Event Discovery** pipeline (not article summaries)
- Creates news-style coverage (no "According to..." language)
- Includes timing markers, facts, and analysis

### 4. **Saves to Database**
Writes to TWO tables:
- `podcasts` - Main podcast record
- `podcast_topics` - Consolidated topics for follow-up queries

---

## Complete Example Flow

### Step 1: Add User Interests (if not exists)

```bash
# Add interests for user
POST /api/users/0ab3d613-b53b-41f0-9442-47c9e05cf636/interests

Body:
{
  "interest": "artificial intelligence",
  "weight": 1.0
}
```

### Step 2: Generate News Podcast

```bash
POST /api/podcasts/generate-news?user_id=0ab3d613-b53b-41f0-9442-47c9e05cf636&duration_minutes=5
```

Response:
```json
{
  "podcast_id": "abc123",
  "status": "generating",
  "estimated_completion_time": "2025-10-26T18:45:00Z",
  "message": "Generating personalized news podcast covering: artificial intelligence"
}
```

### Step 3: Check Status

```bash
GET /api/podcasts/abc123/status
```

Response:
```json
{
  "podcast_id": "abc123",
  "status": "ready",  // or "generating", "failed"
  "progress": 100,
  "message": "Podcast generation complete"
}
```

### Step 4: Get Podcast

```bash
GET /api/podcasts/abc123
```

Response includes:
- Full script
- Sources used
- Fact checks
- Interactive elements
- Generation metadata

### Step 5: Query Topics for Follow-ups

```sql
-- Get topics for this podcast
SELECT * FROM podcast_topics 
WHERE podcast_id = 'abc123'

-- Results: ~4-5 consolidated topics like:
-- "OpenAI Developments" (entity)
-- "AI in Healthcare" (theme)
-- "AI Policy & Regulation" (theme)
```

---

## Frontend Integration

### React Example

```typescript
import axios from 'axios';

async function generateNewsPodcast(userId: string, durationMinutes: number = 5) {
  try {
    // Start generation
    const response = await axios.post(
      `/api/podcasts/generate-news`,
      null,
      {
        params: {
          user_id: userId,
          duration_minutes: durationMinutes
        }
      }
    );
    
    const { podcast_id, estimated_completion_time } = response.data;
    
    // Poll for completion
    const checkStatus = setInterval(async () => {
      const statusRes = await axios.get(`/api/podcasts/${podcast_id}/status`);
      
      if (statusRes.data.status === 'ready') {
        clearInterval(checkStatus);
        
        // Get final podcast
        const podcast = await axios.get(`/api/podcasts/${podcast_id}`);
        console.log('Podcast ready!', podcast.data);
      } else if (statusRes.data.status === 'failed') {
        clearInterval(checkStatus);
        console.error('Generation failed');
      }
    }, 10000); // Check every 10 seconds
    
  } catch (error) {
    console.error('Failed to generate podcast:', error);
  }
}

// Usage
generateNewsPodcast('user-uuid-here', 5);
```

### Swift/iOS Example

```swift
func generateNewsPodcast(userId: String, durationMinutes: Int = 5) async throws {
    let url = URL(string: "http://localhost:8000/api/podcasts/generate-news?user_id=\(userId)&duration_minutes=\(durationMinutes)")!
    
    var request = URLRequest(url: url)
    request.httpMethod = "POST"
    
    let (data, _) = try await URLSession.shared.data(for: request)
    let response = try JSONDecoder().decode(PodcastGenerationResponse.self, from: data)
    
    print("Podcast generating: \(response.podcast_id)")
    
    // Poll for status
    try await pollPodcastStatus(podcastId: response.podcast_id)
}
```

---

## Database Schema Requirements

### Required Tables

**users**
```sql
CREATE TABLE users (
  id UUID PRIMARY KEY,
  email TEXT,
  occupation TEXT,
  complexity_level TEXT DEFAULT 'intermediate',
  tone TEXT DEFAULT 'conversational',
  pace TEXT DEFAULT 'moderate',
  voice_preference TEXT DEFAULT 'single'
);
```

**user_interests**
```sql
CREATE TABLE user_interests (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  interest TEXT NOT NULL,
  weight FLOAT DEFAULT 0.5,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

**podcasts** (already exists)

**podcast_topics** (already exists)

---

## Performance

### Typical Generation Time

- **Research**: 2-3 minutes (event discovery, web search)
- **Script Generation**: 30-60 seconds
- **Database Save**: 1-2 seconds
- **Total**: ~3-4 minutes

### Optimization

With caching enabled:
- **First generation**: 3-4 minutes
- **Repeated topics**: 1-2 minutes (cached search results)

---

## Error Handling

### Common Issues

1. **"User not found"**
   - Ensure user exists in `users` table
   - Check UUID format

2. **"No interests found"**
   - Add interests via `POST /users/{user_id}/interests`
   - Ensure at least 1 interest with weight > 0

3. **"Generation timeout"**
   - Check Claude API key is valid
   - Verify Supabase connection
   - Check logs for specific errors

---

## Testing

```bash
# Run the test
cd /Users/Tim/Desktop/Berkeley/hackathon/feedcast/backend
python test_full_end_to_end.py

# Expected output:
# ✅ Podcast generated and saved successfully!
# ✅ Topics saved: 4 consolidated topics
# ✅ Both 'podcasts' and 'podcast_topics' tables populated!
```

---

## Next Steps

1. **Add Interests** - Ensure users have interests in the database
2. **Call Endpoint** - Make POST request to `/api/podcasts/generate-news`
3. **Poll Status** - Check `/api/podcasts/{id}/status` until ready
4. **Retrieve Podcast** - GET `/api/podcasts/{id}` for full content
5. **Enable Follow-ups** - Query `podcast_topics` for user follow-up questions

---

**Endpoint**: `POST /api/podcasts/generate-news`  
**Status**: ✅ Production Ready  
**Last Updated**: October 26, 2025

