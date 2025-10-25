# Feedcast 🎙️

An AI-personalized podcast application for iOS that generates custom podcast content daily or on-demand based on user interests.

## 📱 Overview

Feedcast is an innovative iOS app built for hackathons that combines AI-generated content with an intuitive podcast listening experience. Users can manage their interests, listen to personalized podcasts, and interact with an AI assistant that understands the podcast context.

### Key Features

- **AI-Generated Podcasts**: Daily personalized podcasts based on user interests
- **On-Demand Generation**: Request custom podcasts for specific topics
- **Integrated Chat**: Ask questions about podcasts while listening
- **Interest Management**: Curate topics that shape your content
- **Beautiful UI**: Inspired by Apple Books and Podcasts apps
- **Smart Playback**: Resume where you left off, adjust speed, skip controls

## 🏗️ Architecture

The app follows the **MVVM (Model-View-ViewModel)** pattern with a clean separation of concerns:

```
feedcast/
├── Models/                 # Data structures
│   ├── Podcast.swift      # Podcast and Episode models
│   ├── Interest.swift     # User interest/topic model
│   ├── ChatMessage.swift  # Chat conversation models
│   └── User.swift         # User profile and playback state
│
├── Services/              # Business logic and data management
│   ├── PodcastService.swift    # Podcast CRUD operations
│   ├── ChatService.swift       # Chat conversation management
│   └── UserService.swift       # User profile and preferences
│
├── ViewModels/            # State management
│   ├── LibraryViewModel.swift    # Library/home screen state
│   ├── PlayerViewModel.swift     # Player and chat state
│   └── InterestsViewModel.swift  # Interest management state
│
├── Views/                 # SwiftUI views
│   ├── LibraryView.swift        # Main podcast library
│   ├── PlayerView.swift         # Podcast player with chat
│   ├── InterestsView.swift      # Interest management
│   └── ContentView.swift        # Root tab view
│
└── Assets.xcassets/       # Images and colors
```

## 🔧 Current Implementation

### Data Layer (Models)

**Podcast & Episode**
- `Podcast`: Represents an AI-generated podcast with metadata, episodes, and interests
- `Episode`: Individual episodes within a podcast with audio URL support

**User & Interests**
- `User`: User profile with preferences and settings
- `Interest`: Topics/categories that personalize content generation
- `PlaybackState`: Resume playback across sessions

**Chat**
- `ChatMessage`: Messages between user and AI
- `Conversation`: Chat history per podcast
- Context-aware responses based on podcast content

### Service Layer

All services are currently using **dummy data** for hackathon prototyping:

**PodcastService** (`Services/PodcastService.swift`)
- Manages podcast library
- Currently returns mock podcasts
- **TODO**: Integrate with backend for real data
- **Future**: Connect to FetchAI for content generation

**ChatService** (`Services/ChatService.swift`)
- Handles chat conversations
- Simple rule-based responses for demo
- **TODO**: Integrate FetchAI for intelligent responses
- **Future**: Add streaming responses for better UX

**UserService** (`Services/UserService.swift`)
- Manages user profile and interests
- Local storage only
- **TODO**: Integrate Supabase Auth
- **Future**: Add iCloud sync for cross-device

### ViewModels

**LibraryViewModel**
- Manages podcast library state
- Filtering, sorting, and search
- Podcast generation requests

**PlayerViewModel**
- Playback controls and state
- Simulated audio playback (timer-based)
- Integrated chat functionality
- **TODO**: Replace with LiveKit audio streaming

**InterestsViewModel**
- CRUD operations for user interests
- Category-based organization
- Active/inactive interest toggling

## 🎨 UI/UX Design

### Library View
- Grid layout inspired by Apple Books
- Featured daily podcast card
- Sort and filter capabilities
- Pull-to-refresh support

### Player View
- Large album artwork
- Playback controls (play/pause, skip, speed)
- Progress tracking
- Episode list
- Collapsible chat interface

### Interests View
- Category browsing
- Active/inactive interest states
- Add/remove interests
- Search and filter

## 🔌 Integration Points for Future Development

### 1. LiveKit Integration (Audio Streaming)

**File**: `ViewModels/PlayerViewModel.swift`

```swift
// TODO: Replace simulated playback with LiveKit
func startPlayback() {
    // Initialize LiveKit room
    // Connect to audio stream
    // Handle playback events
}
```

**Key Integration Areas:**
- Real-time audio streaming
- Low-latency playback
- Background audio support
- Network resilience

### 2. FetchAI Integration (Content Generation)

**File**: `Services/PodcastService.swift`

```swift
// TODO: Integrate FetchAI for podcast generation
func generatePodcast(interests: [Interest], prompt: String?) async throws -> Podcast {
    // 1. Send user interests to FetchAI agent
    // 2. Receive structured podcast content
    // 3. Parse and create Podcast model
    // 4. Return generated podcast
}
```

**File**: `Services/ChatService.swift`

```swift
// TODO: Integrate FetchAI for intelligent chat
func sendMessage(...) async throws -> ChatMessage {
    // 1. Send message with podcast context to FetchAI
    // 2. Stream or receive AI response
    // 3. Create and return ChatMessage
}
```

**Key Integration Areas:**
- Daily podcast content generation
- On-demand topic-based generation
- Context-aware chat responses
- Transcript analysis for better answers

### 3. Supabase Backend Integration

**Authentication** (`Services/UserService.swift`)
```swift
// TODO: Add Supabase Auth
func signIn(email: String, password: String) async throws -> User
func signUp(email: String, password: String) async throws -> User
func signOut() async throws
```

**Database Schema Recommendations:**

```sql
-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email TEXT UNIQUE NOT NULL,
    name TEXT,
    daily_podcast_enabled BOOLEAN DEFAULT true,
    daily_podcast_time TIME,
    created_at TIMESTAMP DEFAULT NOW()
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

-- Podcasts table
CREATE TABLE podcasts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT,
    cover_image_url TEXT,
    interests TEXT[],
    is_daily BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW()
);

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

-- Chat messages table
CREATE TABLE chat_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    podcast_id UUID REFERENCES podcasts(id) ON DELETE CASCADE,
    episode_id UUID REFERENCES episodes(id),
    content TEXT NOT NULL,
    sender TEXT NOT NULL CHECK (sender IN ('user', 'ai')),
    timestamp TIMESTAMP DEFAULT NOW()
);

-- Playback states table
CREATE TABLE playback_states (
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    podcast_id UUID REFERENCES podcasts(id) ON DELETE CASCADE,
    episode_id UUID REFERENCES episodes(id) ON DELETE CASCADE,
    current_time REAL NOT NULL,
    last_played TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (user_id, podcast_id)
);
```

**API Integration Points:**
- User authentication and session management
- Podcast CRUD operations
- Interest synchronization
- Chat history persistence
- Playback state sync

### 4. Audio Enhancement

**Considerations:**
- Offline playback and caching
- Background audio continuation
- AirPlay and CarPlay support
- Audio session management
- Remote control integration

## 🚀 Getting Started

### Prerequisites
- Xcode 15.0 or later
- iOS 17.0 or later
- Swift 5.9+

### Running the App

1. **Open the project**
   ```bash
   cd feedcast
   open feedcast.xcodeproj
   ```

2. **Select a simulator or device**
   - Choose iPhone 15 or later for best experience

3. **Build and run**
   - Press `⌘ + R` or click the Run button

### Current Demo Features

The app currently runs with dummy data:
- 4 pre-populated podcasts
- 6 default user interests
- Simulated audio playback
- Basic chat responses

## 📝 Development Roadmap

### Phase 1: Core Features ✅ (Current)
- [x] Basic app structure and navigation
- [x] Podcast library with grid layout
- [x] Player UI with controls
- [x] Interest management
- [x] Integrated chat interface
- [x] Dummy data for prototyping

### Phase 2: Backend Integration 🔄 (Next)
- [ ] Supabase authentication
- [ ] Database schema implementation
- [ ] API integration for all services
- [ ] User session management
- [ ] Data synchronization

### Phase 3: AI Integration 🎯
- [ ] FetchAI agent setup
- [ ] Podcast content generation
- [ ] Intelligent chat responses
- [ ] Context-aware recommendations
- [ ] Daily podcast automation

### Phase 4: Audio Streaming 🎵
- [ ] LiveKit integration
- [ ] Real-time audio playback
- [ ] Background audio support
- [ ] Playback quality controls
- [ ] Offline caching

### Phase 5: Polish & Enhancement ✨
- [ ] Custom podcast covers (AI-generated)
- [ ] Social sharing features
- [ ] Analytics and insights
- [ ] Push notifications for daily podcasts
- [ ] iPad and Mac support

## 🤖 AI Integration Details

### FetchAI Integration Strategy

**Podcast Generation Workflow:**
1. User interests are sent to FetchAI agent
2. Agent queries relevant news, articles, and data sources
3. Content is structured into podcast script format
4. Text-to-speech conversion (potential: ElevenLabs integration)
5. Audio returned and stored via LiveKit

**Chat Interaction Workflow:**
1. User message sent with podcast context (transcript, metadata)
2. FetchAI agent analyzes context and user query
3. Intelligent response generated based on content
4. Streaming response for better UX
5. Conversation history maintained for context

### LiveKit Integration Strategy

**Audio Streaming Setup:**
- Create LiveKit room per podcast generation session
- Stream audio in real-time as it's generated
- Support pause/resume with buffering
- Handle network interruptions gracefully

**Recommended Configuration:**
```swift
// Example LiveKit setup
let room = Room()
room.connect(url: liveKitURL, token: accessToken)

// Subscribe to audio tracks
room.onTrackSubscribed = { track, publication, participant in
    if let audioTrack = track as? RemoteAudioTrack {
        // Play audio track
    }
}
```

## 🧪 Testing Notes

### Manual Testing Checklist
- [ ] Library loads with dummy podcasts
- [ ] Podcast playback controls work
- [ ] Chat interface opens and sends messages
- [ ] Interests can be added/removed
- [ ] Search and filtering work correctly
- [ ] Navigation between views is smooth

### Future Automated Testing
- Unit tests for ViewModels
- Service layer integration tests
- UI tests for critical flows
- API integration tests with Supabase

## 🔐 Security Considerations

### For Backend Integration
- [ ] Implement proper authentication flows
- [ ] Secure API key storage (not in code)
- [ ] Use environment variables for sensitive data
- [ ] Implement proper session management
- [ ] Add rate limiting for API calls
- [ ] Validate all user inputs

### Data Privacy
- [ ] User data stored securely in Supabase
- [ ] Chat history encrypted at rest
- [ ] GDPR compliance for user data
- [ ] Clear data deletion policies

## 📖 Documentation for LLMs

### Context for Future Development

**For adding new features:**
1. Models go in `feedcast/Models/`
2. Business logic in `feedcast/Services/`
3. State management in `feedcast/ViewModels/`
4. UI in `feedcast/Views/`

**For backend integration:**
- All services have clear TODO comments
- Service methods use async/await pattern
- Error handling is implemented
- Mock data can be easily replaced

**For AI integration:**
- See integration points section above
- Services are ready for async API calls
- Models support all necessary fields

**Key Design Patterns:**
- MVVM architecture throughout
- Combine for reactive programming
- SwiftUI for declarative UI
- Async/await for asynchronous operations

## 🤝 Contributing

This is a hackathon project. For team members:
1. Follow the existing architecture
2. Add TODO comments for future work
3. Keep models immutable (struct-based)
4. Use meaningful variable names
5. Document integration points

## 📄 License

This project is created for hackathon purposes.

## 📧 Contact

For questions or collaboration, reach out to the development team.

---

**Built with** ❤️ **for the hackathon using SwiftUI**

*Ready for LiveKit, FetchAI, and Supabase integration!*

