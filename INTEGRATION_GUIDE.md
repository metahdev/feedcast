# Integration Guide 🔌

This document provides step-by-step instructions for integrating LiveKit, FetchAI, and Supabase into the Feedcast app.

## Table of Contents
1. [Supabase Backend Setup](#supabase-backend-setup)
2. [FetchAI Integration](#fetchai-integration)
3. [LiveKit Audio Streaming](#livekit-audio-streaming)
4. [Environment Configuration](#environment-configuration)

---

## Supabase Backend Setup

### 1. Create Supabase Project

1. Go to [supabase.com](https://supabase.com)
2. Create a new project
3. Note your project URL and anon key

### 2. Database Schema

Execute the following SQL in Supabase SQL Editor:

```sql
-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email TEXT UNIQUE NOT NULL,
    name TEXT,
    daily_podcast_enabled BOOLEAN DEFAULT true,
    daily_podcast_time TIME,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Interests table
CREATE TABLE interests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    is_active BOOLEAN DEFAULT true,
    added_at TIMESTAMP DEFAULT NOW()
);

-- Create index for faster queries
CREATE INDEX idx_interests_user_id ON interests(user_id);
CREATE INDEX idx_interests_active ON interests(is_active);

-- Podcasts table
CREATE TABLE podcasts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT,
    cover_image_url TEXT,
    interests TEXT[] DEFAULT '{}',
    is_daily BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create index
CREATE INDEX idx_podcasts_user_id ON podcasts(user_id);
CREATE INDEX idx_podcasts_created_at ON podcasts(created_at DESC);

-- Episodes table
CREATE TABLE episodes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    podcast_id UUID REFERENCES podcasts(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT,
    duration REAL NOT NULL,
    audio_url TEXT,
    transcript TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create index
CREATE INDEX idx_episodes_podcast_id ON episodes(podcast_id);

-- Chat messages table
CREATE TABLE chat_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    podcast_id UUID REFERENCES podcasts(id) ON DELETE CASCADE,
    episode_id UUID REFERENCES episodes(id),
    content TEXT NOT NULL,
    sender TEXT NOT NULL CHECK (sender IN ('user', 'ai')),
    timestamp TIMESTAMP DEFAULT NOW()
);

-- Create index
CREATE INDEX idx_chat_messages_podcast_id ON chat_messages(podcast_id);
CREATE INDEX idx_chat_messages_timestamp ON chat_messages(timestamp);

-- Playback states table
CREATE TABLE playback_states (
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    podcast_id UUID REFERENCES podcasts(id) ON DELETE CASCADE,
    episode_id UUID REFERENCES episodes(id) ON DELETE CASCADE,
    current_time REAL NOT NULL,
    last_played TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (user_id, podcast_id)
);

-- RLS (Row Level Security) Policies
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE interests ENABLE ROW LEVEL SECURITY;
ALTER TABLE podcasts ENABLE ROW LEVEL SECURITY;
ALTER TABLE episodes ENABLE ROW LEVEL SECURITY;
ALTER TABLE chat_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE playback_states ENABLE ROW LEVEL SECURITY;

-- Users can only see their own data
CREATE POLICY "Users can view own data" ON users
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update own data" ON users
    FOR UPDATE USING (auth.uid() = id);

-- Interests policies
CREATE POLICY "Users can view own interests" ON interests
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own interests" ON interests
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own interests" ON interests
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own interests" ON interests
    FOR DELETE USING (auth.uid() = user_id);

-- Similar policies for other tables
CREATE POLICY "Users can view own podcasts" ON podcasts
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own podcasts" ON podcasts
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete own podcasts" ON podcasts
    FOR DELETE USING (auth.uid() = user_id);

-- Episodes (accessible through podcast ownership)
CREATE POLICY "Users can view episodes of own podcasts" ON episodes
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM podcasts 
            WHERE podcasts.id = episodes.podcast_id 
            AND podcasts.user_id = auth.uid()
        )
    );

-- Chat messages
CREATE POLICY "Users can view own chat messages" ON chat_messages
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM podcasts 
            WHERE podcasts.id = chat_messages.podcast_id 
            AND podcasts.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can insert own chat messages" ON chat_messages
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM podcasts 
            WHERE podcasts.id = chat_messages.podcast_id 
            AND podcasts.user_id = auth.uid()
        )
    );

-- Playback states
CREATE POLICY "Users can view own playback states" ON playback_states
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can upsert own playback states" ON playback_states
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own playback states" ON playback_states
    FOR UPDATE USING (auth.uid() = user_id);
```

### 3. Swift Integration

#### Install Supabase SDK

Add to your Xcode project via Swift Package Manager:
- URL: `https://github.com/supabase/supabase-swift`
- Version: Latest

#### Create Supabase Client

Create `Services/SupabaseClient.swift`:

```swift
import Foundation
import Supabase

class SupabaseClient {
    static let shared = SupabaseClient()
    
    let client: SupabaseClient
    
    private init() {
        client = SupabaseClient(
            supabaseURL: URL(string: Config.supabaseURL)!,
            supabaseKey: Config.supabaseAnonKey
        )
    }
}
```

#### Update UserService

Replace dummy auth in `Services/UserService.swift`:

```swift
func signIn(email: String, password: String) async throws -> User {
    let session = try await SupabaseClient.shared.client.auth.signIn(
        email: email,
        password: password
    )
    
    // Fetch user data from database
    let userData: User = try await SupabaseClient.shared.client
        .from("users")
        .select()
        .eq("id", value: session.user.id)
        .single()
        .execute()
        .value
    
    currentUser = userData
    return userData
}

func signUp(email: String, password: String, name: String) async throws -> User {
    let session = try await SupabaseClient.shared.client.auth.signUp(
        email: email,
        password: password
    )
    
    // Create user record
    let newUser = User(
        id: session.user.id.uuidString,
        name: name,
        email: email
    )
    
    try await SupabaseClient.shared.client
        .from("users")
        .insert(newUser)
        .execute()
    
    currentUser = newUser
    return newUser
}
```

---

## FetchAI Integration

### 1. Setup FetchAI Agent

1. Create account at [fetch.ai](https://fetch.ai)
2. Set up an agent for podcast generation
3. Configure agent with access to news APIs, content sources

### 2. Agent Configuration

Your FetchAI agent should:
- Accept user interests as input
- Query relevant content sources
- Structure output as JSON with podcast metadata
- Generate episode scripts

Example agent response format:

```json
{
  "title": "AI & Tech Weekly",
  "description": "Your personalized briefing on AI and technology",
  "interests": ["AI", "Technology"],
  "episodes": [
    {
      "title": "AI Breakthroughs",
      "description": "Latest in artificial intelligence",
      "script": "Welcome to today's podcast...",
      "duration": 420
    }
  ]
}
```

### 3. iOS Integration

Create `Services/FetchAIService.swift`:

```swift
import Foundation

class FetchAIService {
    static let shared = FetchAIService()
    private let baseURL = Config.fetchAIBaseURL
    private let apiKey = Config.fetchAIAPIKey
    
    func generatePodcast(interests: [Interest], prompt: String? = nil) async throws -> PodcastGenerationResponse {
        var request = URLRequest(url: URL(string: "\(baseURL)/generate-podcast")!)
        request.httpMethod = "POST"
        request.setValue("Bearer \(apiKey)", forHTTPHeaderField: "Authorization")
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        let payload = PodcastGenerationRequest(
            interests: interests.map { $0.name },
            customPrompt: prompt
        )
        
        request.httpBody = try JSONEncoder().encode(payload)
        
        let (data, response) = try await URLSession.shared.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse,
              httpResponse.statusCode == 200 else {
            throw FetchAIError.generationFailed
        }
        
        return try JSONDecoder().decode(PodcastGenerationResponse.self, from: data)
    }
    
    func generateChatResponse(
        message: String,
        context: PodcastContext
    ) async throws -> String {
        var request = URLRequest(url: URL(string: "\(baseURL)/chat")!)
        request.httpMethod = "POST"
        request.setValue("Bearer \(apiKey)", forHTTPHeaderField: "Authorization")
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        let payload = ChatRequest(
            message: message,
            podcastTitle: context.title,
            transcript: context.transcript,
            conversationHistory: context.previousMessages
        )
        
        request.httpBody = try JSONEncoder().encode(payload)
        
        let (data, response) = try await URLSession.shared.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse,
              httpResponse.statusCode == 200 else {
            throw FetchAIError.chatFailed
        }
        
        let chatResponse = try JSONDecoder().decode(ChatResponse.self, from: data)
        return chatResponse.message
    }
}

// Supporting types
struct PodcastGenerationRequest: Codable {
    let interests: [String]
    let customPrompt: String?
}

struct PodcastGenerationResponse: Codable {
    let title: String
    let description: String
    let interests: [String]
    let episodes: [EpisodeScript]
}

struct EpisodeScript: Codable {
    let title: String
    let description: String
    let script: String
    let duration: TimeInterval
}

struct ChatRequest: Codable {
    let message: String
    let podcastTitle: String
    let transcript: String?
    let conversationHistory: [String]
}

struct ChatResponse: Codable {
    let message: String
}

struct PodcastContext {
    let title: String
    let transcript: String?
    let previousMessages: [String]
}

enum FetchAIError: Error {
    case generationFailed
    case chatFailed
}
```

### 4. Update PodcastService

In `Services/PodcastService.swift`, replace dummy generation:

```swift
func generatePodcast(interests: [Interest], prompt: String? = nil) async throws -> Podcast {
    isLoading = true
    defer { isLoading = false }
    
    // Call FetchAI
    let response = try await FetchAIService.shared.generatePodcast(
        interests: interests,
        prompt: prompt
    )
    
    // Convert scripts to episodes (with audio generation)
    var episodes: [Episode] = []
    for episodeScript in response.episodes {
        // Generate audio from script (see next section)
        let audioURL = try await generateAudio(from: episodeScript.script)
        
        let episode = Episode(
            title: episodeScript.title,
            description: episodeScript.description,
            duration: episodeScript.duration,
            audioURL: audioURL,
            transcript: episodeScript.script
        )
        episodes.append(episode)
    }
    
    let podcast = Podcast(
        title: response.title,
        description: response.description,
        interests: response.interests,
        episodes: episodes,
        isDaily: false
    )
    
    // Save to Supabase
    try await savePodcastToBackend(podcast)
    
    await MainActor.run {
        podcasts.insert(podcast, at: 0)
    }
    
    return podcast
}
```

---

## LiveKit Audio Streaming

### 1. Setup LiveKit

1. Create account at [livekit.io](https://livekit.io)
2. Create a project and note your URL and API keys
3. Set up a server component for audio generation

### 2. Install LiveKit SDK

Add to Xcode via Swift Package Manager:
- URL: `https://github.com/livekit/client-sdk-swift`
- Version: Latest

### 3. Audio Generation Server

You'll need a server that:
- Receives text script from iOS app
- Converts text to speech (e.g., ElevenLabs, Google TTS)
- Streams audio via LiveKit

Example server endpoint (Node.js):

```javascript
app.post('/generate-audio', async (req, res) => {
  const { script, episodeId } = req.body;
  
  // Create LiveKit room
  const room = await livekit.createRoom(episodeId);
  
  // Convert text to speech (using ElevenLabs, etc.)
  const audioStream = await textToSpeech(script);
  
  // Publish audio to room
  await room.publishAudio(audioStream);
  
  res.json({ roomUrl: room.url, token: room.token });
});
```

### 4. iOS Integration

Create `Services/AudioStreamingService.swift`:

```swift
import LiveKit
import AVFoundation

class AudioStreamingService: ObservableObject {
    static let shared = AudioStreamingService()
    
    private var room: Room?
    private var audioTrack: RemoteAudioTrack?
    
    @Published var isConnected = false
    @Published var isPlaying = false
    
    func connectToRoom(roomUrl: String, token: String) async throws {
        room = Room()
        
        try await room?.connect(
            url: roomUrl,
            token: token
        )
        
        // Handle track subscription
        room?.onTrackSubscribed = { [weak self] track, publication, participant in
            if let audioTrack = track as? RemoteAudioTrack {
                self?.audioTrack = audioTrack
                self?.isConnected = true
            }
        }
    }
    
    func play() {
        audioTrack?.start()
        isPlaying = true
    }
    
    func pause() {
        audioTrack?.stop()
        isPlaying = false
    }
    
    func seek(to time: TimeInterval) {
        // Implement seek functionality
        // May require server-side support
    }
    
    func disconnect() {
        room?.disconnect()
        room = nil
        audioTrack = nil
        isConnected = false
        isPlaying = false
    }
}
```

### 5. Update PlayerViewModel

In `ViewModels/PlayerViewModel.swift`:

```swift
private let audioService = AudioStreamingService.shared

func startPlayback() {
    Task {
        if !audioService.isConnected {
            // Get LiveKit room info for this episode
            let roomInfo = try await getAudioRoomInfo(episodeId: currentEpisode.id)
            try await audioService.connectToRoom(
                roomUrl: roomInfo.url,
                token: roomInfo.token
            )
        }
        
        audioService.play()
        await MainActor.run {
            isPlaying = true
        }
    }
}

func pausePlayback() {
    audioService.pause()
    isPlaying = false
}

private func getAudioRoomInfo(episodeId: String) async throws -> RoomInfo {
    // Call your backend to get LiveKit room details
    let url = URL(string: "\(Config.backendURL)/audio-room/\(episodeId)")!
    let (data, _) = try await URLSession.shared.data(from: url)
    return try JSONDecoder().decode(RoomInfo.self, from: data)
}

struct RoomInfo: Codable {
    let url: String
    let token: String
}
```

---

## Environment Configuration

### 1. Create Config File

Create `Config.swift`:

```swift
import Foundation

enum Config {
    // Supabase
    static let supabaseURL = getEnvironmentVariable("SUPABASE_URL")
    static let supabaseAnonKey = getEnvironmentVariable("SUPABASE_ANON_KEY")
    
    // FetchAI
    static let fetchAIBaseURL = getEnvironmentVariable("FETCHAI_BASE_URL")
    static let fetchAIAPIKey = getEnvironmentVariable("FETCHAI_API_KEY")
    
    // LiveKit
    static let liveKitURL = getEnvironmentVariable("LIVEKIT_URL")
    static let liveKitAPIKey = getEnvironmentVariable("LIVEKIT_API_KEY")
    static let liveKitAPISecret = getEnvironmentVariable("LIVEKIT_API_SECRET")
    
    // Backend
    static let backendURL = getEnvironmentVariable("BACKEND_URL")
    
    private static func getEnvironmentVariable(_ key: String) -> String {
        guard let value = ProcessInfo.processInfo.environment[key] else {
            fatalError("Missing environment variable: \(key)")
        }
        return value
    }
}
```

### 2. Environment Setup

Create `.env` file (add to `.gitignore`):

```bash
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key

# FetchAI
FETCHAI_BASE_URL=https://your-fetchai-endpoint.com
FETCHAI_API_KEY=your-api-key

# LiveKit
LIVEKIT_URL=wss://your-livekit-server.com
LIVEKIT_API_KEY=your-api-key
LIVEKIT_API_SECRET=your-api-secret

# Backend
BACKEND_URL=https://your-backend.com
```

### 3. Xcode Configuration

1. Add environment variables to your scheme:
   - Edit Scheme → Run → Arguments → Environment Variables
   - Add each variable from `.env`

2. Or use a build script to load from `.env`:
   - Add Run Script Phase in Build Phases
   - Source `.env` file and export variables

---

## Testing Integration

### 1. Test Supabase Connection

```swift
// Add this to test Supabase
func testSupabaseConnection() async {
    do {
        let response = try await SupabaseClient.shared.client
            .from("users")
            .select()
            .limit(1)
            .execute()
        print("✅ Supabase connected successfully")
    } catch {
        print("❌ Supabase connection failed: \(error)")
    }
}
```

### 2. Test FetchAI

```swift
func testFetchAI() async {
    do {
        let testInterests = [
            Interest(name: "AI", category: .technology)
        ]
        let response = try await FetchAIService.shared.generatePodcast(
            interests: testInterests
        )
        print("✅ FetchAI generated podcast: \(response.title)")
    } catch {
        print("❌ FetchAI failed: \(error)")
    }
}
```

### 3. Test LiveKit

```swift
func testLiveKit() async {
    do {
        try await AudioStreamingService.shared.connectToRoom(
            roomUrl: "your-test-room-url",
            token: "your-test-token"
        )
        print("✅ LiveKit connected successfully")
    } catch {
        print("❌ LiveKit connection failed: \(error)")
    }
}
```

---

## Deployment Checklist

- [ ] Supabase project created and configured
- [ ] Database schema deployed
- [ ] RLS policies tested
- [ ] FetchAI agent configured and tested
- [ ] LiveKit server setup
- [ ] Audio generation pipeline working
- [ ] Environment variables configured
- [ ] API keys secured (not in code)
- [ ] Error handling implemented
- [ ] Rate limiting considered
- [ ] Offline support planned
- [ ] App tested end-to-end

---

## Troubleshooting

### Supabase Issues
- **Auth errors**: Check RLS policies are correct
- **Connection errors**: Verify URL and API key
- **Timeout**: Check network connectivity

### FetchAI Issues
- **Generation fails**: Check API quota and rate limits
- **Slow responses**: Implement loading indicators
- **Invalid format**: Validate response schema

### LiveKit Issues
- **Audio not playing**: Check track subscription
- **Connection drops**: Implement reconnection logic
- **Latency**: Adjust buffer settings

---

For questions or issues during integration, refer to official documentation:
- [Supabase Docs](https://supabase.com/docs)
- [FetchAI Docs](https://docs.fetch.ai)
- [LiveKit Docs](https://docs.livekit.io)

