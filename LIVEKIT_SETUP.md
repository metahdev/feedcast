# LiveKit Voice Chat Setup - Cal Hacks Quickstart

## 🎉 Cal Hacks 12.0 Instructions

This guide follows the official LiveKit hackathon starter kit to get voice chat working quickly!

## Step 1: Setup LiveKit Cloud (2 minutes)

### 1.1 Create Account
1. Go to https://cloud.livekit.io
2. Sign up for a free account
3. Create a new project

### 1.2 Redeem Free Trial
1. Go to https://cloud.livekit.io/projects/p_/redeem
2. Enter code: **`LIVEKIT-CALHACKS`**
3. Get free "ship" tier (no credit card required!)

### 1.3 Get Credentials
1. Go to your project settings
2. Copy these values:
   - **URL**: `wss://your-project.livekit.cloud`
   - **API Key**: `APIxxxxx`
   - **API Secret**: `xxxxxxxx`

### 1.4 Update iOS Config
Open `feedcast/Config.swift` and update:

```swift
static let liveKitURL = "wss://your-project.livekit.cloud"
static let liveKitAPIKey = "APIxxxxx"
static let liveKitSecretKey = "your-secret"
```

## Step 2: Install LiveKit CLI (1 minute)

**macOS:**
```bash
brew install livekit-cli
```

**Linux:**
```bash
curl -sSL https://get.livekit.io/cli | bash
```

**Verify:**
```bash
lk --version
```

## Step 3: Authenticate CLI (1 minute)

```bash
lk cloud auth
```

This opens a browser to authenticate and link your project.

## Step 4: Create Agent (2 minutes)

```bash
# Create a new agent from boilerplate
lk app create

# When prompted:
# - Select: agent-starter-python (no quotes, use arrow keys)
# - Name it: feedcast-voice-agent
```

This creates a directory with everything you need!

## Step 4.5: Create Token Server (2 minutes)

```bash
# Create token server in a separate directory
lk app create

# When prompted:
# - Select: token-server
# - Name it: feedcast-token-server
```

The token server generates JWT tokens for your iOS app to connect to rooms.

## Step 5: Setup Agent for Podcast Chat (5 minutes)

```bash
cd feedcast-voice-agent
```

### 5.1 Install Dependencies
```bash
uv sync
```

### 5.2 Download Model Files
```bash
uv run src/agent.py download-files
```

### 5.3 Customize Agent for Podcast Context

Edit `src/agent.py` to add podcast context awareness:

```python
from dotenv import load_dotenv

from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions
from livekit.plugins import noise_cancellation, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

load_dotenv(".env.local")

class PodcastAssistant(Agent):
    def __init__(self, podcast_context: dict = None) -> None:
        # Build context-aware instructions
        if podcast_context:
            instructions = f"""You are a helpful voice AI assistant discussing the podcast 
            '{podcast_context.get('title', 'Unknown Podcast')}'.
            
            Podcast description: {podcast_context.get('description', 'N/A')}
            Topics covered: {', '.join(podcast_context.get('interests', []))}
            
            Recent episode: {podcast_context.get('current_episode', 'N/A')}
            
            You eagerly help users understand and discuss this podcast content.
            Your responses are concise, conversational, and perfect for voice (1-2 sentences).
            You are curious, friendly, and engaging."""
        else:
            instructions = """You are a helpful voice AI assistant for podcast discussions.
            You eagerly assist users with questions about podcast content.
            Your responses are concise, to the point, and perfect for voice conversation.
            You are curious, friendly, and have a sense of humor."""
        
        super().__init__(instructions=instructions)

async def entrypoint(ctx: agents.JobContext):
    # Get podcast context from room metadata
    podcast_context = None
    try:
        import json
        if ctx.room.metadata:
            metadata = json.loads(ctx.room.metadata)
            podcast_context = metadata.get('podcast')
    except:
        pass
    
    session = AgentSession(
        stt="assemblyai/universal-streaming:en",
        llm="openai/gpt-4.1-mini",
        tts="cartesia/sonic-2:9626c31c-bec5-4cca-baa8-f8ba9e84c8bc",
        vad=silero.VAD.load(),
        turn_detection=MultilingualModel(),
    )

    await session.start(
        room=ctx.room,
        agent=PodcastAssistant(podcast_context),
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC(), 
        ),
    )

    # Greeting
    greeting = "Greet the user warmly and offer to answer questions."
    if podcast_context:
        greeting = f"Greet the user and offer to discuss the podcast '{podcast_context.get('title')}' with them."
    
    await session.generate_reply(instructions=greeting)

if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))
```

## Step 6: Test Agent Locally (2 minutes)

### Console Mode (Talk to Agent in Terminal)
```bash
uv run src/agent.py console
```

Now you can speak to your agent! Type or speak to test it.

### Dev Mode (Connect to LiveKit Cloud)
```bash
uv run src/agent.py dev
```

Agent is now available via LiveKit Cloud. Test at:
https://cloud.livekit.io/projects/p_/sandbox

## Step 7: iOS App Integration (5 minutes)

### 7.1 Add LiveKit Swift SDK

In Xcode:
1. Go to **File** → **Add Package Dependencies**
2. Enter: `https://github.com/livekit/client-sdk-swift`
3. Select version **2.5.0** or later
4. Add to target: **feedcast**

### 7.2 Add Permissions to Info.plist

Right-click `Info.plist` → **Open As** → **Source Code**, add:

```xml
<key>NSMicrophoneUsageDescription</key>
<string>We need microphone access for voice conversations about podcasts</string>

<key>UIBackgroundModes</key>
<array>
    <string>audio</string>
</array>
```

### 7.3 Setup Token Server

**Option 1: Use the Boilerplate Token Server (Recommended)**

You already created `feedcast-token-server` with `lk app create`. Now set it up:

```bash
cd feedcast-token-server
npm install
npm start
```

The token server runs on `http://localhost:3000` by default.

**Customize it for podcast metadata:**

Edit `src/index.ts` or `index.js` to accept podcast data:

```typescript
app.post('/token', async (req, res) => {
  const { roomName, userName, podcastData } = req.body;
  
  const at = new AccessToken(
    process.env.LIVEKIT_API_KEY,
    process.env.LIVEKIT_API_SECRET,
    {
      identity: userName || `user-${Math.random().toString(36).substring(7)}`,
      metadata: JSON.stringify({ podcast: podcastData }),
    }
  );
  
  at.addGrant({ 
    room: roomName,
    roomJoin: true,
    canPublish: true,
    canSubscribe: true 
  });
  
  res.json({ token: await at.toJwt() });
});
```

**Option 2: Use LiveKit Sandbox (Testing Only)**

For quick testing, use the built-in sandbox:
- URL: `https://cloud.livekit.io/projects/p_YOUR_PROJECT/sandbox`

**Deploy Token Server:**

```bash
# Deploy to Vercel (easiest)
cd feedcast-token-server
vercel deploy
```

Or use Railway, Render, or any Node.js host.

### 7.4 Update VoiceChatView.swift

Add the real LiveKit implementation:

```swift
import LiveKit

class LiveKitVoiceService {
    private var room: Room?
    let podcast: Podcast
    let onTranscript: (String, Bool) -> Void
    let onStateChange: (VoiceState) -> Void
    
    init(podcast: Podcast, onTranscript: @escaping (String, Bool) -> Void, onStateChange: @escaping (VoiceState) -> Void) {
        self.podcast = podcast
        self.onTranscript = onTranscript
        self.onStateChange = onStateChange
    }
    
    func connect() async throws {
        // 1. Generate room name
        let roomName = "podcast-\(podcast.id ?? UUID().uuidString)"
        
        // 2. Get token from your server
        let token = try await fetchToken(roomName: roomName)
        
        // 3. Create room
        room = Room()
        
        // 4. Set delegate
        await room?.add(delegate: self)
        
        // 5. Connect
        try await room?.connect(
            url: Config.liveKitURL,
            token: token,
            connectOptions: ConnectOptions(enableMicrophone: true)
        )
        
        print("✅ Connected to LiveKit room: \(roomName)")
    }
    
    func fetchToken(roomName: String) async throws -> String {
        // Option 1: Use boilerplate token server (development)
        let url = URL(string: "http://localhost:3000/token")!
        
        // Option 2: Use deployed token server (production)
        // let url = URL(string: "https://your-token-server.vercel.app/token")!
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        let body: [String: Any] = [
            "roomName": roomName,
            "userName": "User-\(UUID().uuidString.prefix(8))",
            "podcastData": [
                "title": podcast.title,
                "description": podcast.description,
                "interests": podcast.interests,
                "current_episode": podcast.episodes.first?.title ?? ""
            ]
        ]
        
        request.httpBody = try JSONSerialization.data(withJSONObject: body)
        
        let (data, _) = try await URLSession.shared.data(for: request)
        let response = try JSONDecoder().decode(TokenResponse.self, from: data)
        return response.token
    }
    
    func disconnect() async {
        await room?.disconnect()
        room = nil
    }
}

extension LiveKitVoiceService: RoomDelegate {
    func room(_ room: Room, participantDidJoin participant: RemoteParticipant) {
        print("👤 Participant joined: \(participant.identity ?? "unknown")")
        
        if participant.kind == .agent {
            print("🤖 Agent joined the room!")
            observeAgentState(participant)
        }
    }
    
    func room(_ room: Room, participant: RemoteParticipant, trackDidSubscribe track: Track, publication: TrackPublication) {
        if track.kind == .audio && participant.kind == .agent {
            print("🔊 Agent audio track subscribed - will play automatically")
        }
    }
    
    func observeAgentState(_ participant: RemoteParticipant) {
        // Monitor agent state attribute
        Task { @MainActor in
            for await attributes in participant.attributes {
                if let state = attributes["lk.agent.state"] {
                    print("🤖 Agent state: \(state)")
                    switch state {
                    case "listening":
                        onStateChange(.listening)
                    case "thinking":
                        onStateChange(.processing)
                    case "speaking":
                        onStateChange(.speaking)
                    default:
                        break
                    }
                }
            }
        }
    }
}

struct TokenResponse: Codable {
    let token: String
}
```

## Step 8: Test End-to-End (2 minutes)

### Terminal 1: Run Agent
```bash
cd feedcast-voice-agent
uv run src/agent.py dev
```

### Terminal 2 (Optional): Run Token Server
```bash
npm start
```

### Xcode: Build & Run iOS App
1. Build and run on device (microphone needs real device)
2. Open a podcast
3. Tap the waveform button (top-right)
4. Tap "Start Voice Chat"
5. Allow microphone access
6. Start talking!

## Step 9: Deploy Agent to Cloud (2 minutes)

When ready for production:

```bash
cd feedcast-voice-agent
lk agent create
```

Follow prompts to deploy. Your agent will be available 24/7!

## Troubleshooting

### "LiveKit Not Configured"
- Check `Config.swift` has valid credentials
- Make sure you redeemed the Cal Hacks code

### Agent Not Joining Room
```bash
# Check agent is running
lk agent list

# Check agent logs
lk agent logs YOUR_AGENT_NAME
```

### No Audio on iOS
- Test on **real device** (simulator doesn't have mic)
- Check microphone permissions in Settings
- Verify agent is publishing audio: check logs

### Token Errors
- Verify API key/secret in `.env.local`
- Check token server is running
- Test token generation with: `lk token create`

## Quick Reference

### Create Projects
```bash
# Create agent
lk app create
→ Select: agent-starter-python
→ Name: feedcast-voice-agent

# Create token server  
lk app create
→ Select: token-server
→ Name: feedcast-token-server
```

### Agent Commands
```bash
# Talk to agent locally
cd feedcast-voice-agent
uv run src/agent.py console

# Run in dev mode (connects to cloud)
uv run src/agent.py dev

# Deploy to cloud
lk agent create

# View logs
lk agent logs YOUR_AGENT_NAME

# List agents
lk agent list
```

### Token Server Commands
```bash
# Run locally
cd feedcast-token-server
npm install
npm start

# Deploy to Vercel
vercel deploy
```

### Test Your Agent
- **Sandbox**: https://cloud.livekit.io/projects/p_/sandbox
- **iOS App**: Tap waveform button in player

## Cost Breakdown (with Free Tier)

### Free Trial (Cal Hacks Code)
- ✅ "Ship" tier free
- ✅ Generous limits for hackathon
- ✅ No credit card required

### After Free Trial
Per 5-minute conversation:
- LiveKit: ~$0.001
- STT: ~$0.008
- LLM: ~$0.02-0.05
- TTS: ~$0.01
- **Total**: ~$0.04-0.07 per conversation

## Resources

- **Docs**: https://docs.livekit.io/agents/start/voice-ai
- **Examples**: https://github.com/livekit-examples/python-agents-examples
- **Swift SDK**: https://github.com/livekit/client-sdk-swift
- **Support**: https://livekit.io/discord

## Architecture Diagram

```
┌─────────────────┐
│   iOS App       │  1. User taps waveform button
│   (feedcast)    │  2. Gets token from server
└────────┬────────┘  3. Connects to LiveKit room
         │           4. Publishes microphone audio
         ↓
┌─────────────────┐
│  LiveKit Cloud  │  • WebRTC media server
│                 │  • Routes audio between app & agent
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│  LiveKit Agent  │  1. Receives user audio
│  (Python)       │  2. STT → converts to text
│                 │  3. LLM → generates response (with podcast context)
└─────────────────┘  4. TTS → converts to speech
                     5. Publishes audio back to room
```

## Summary

✅ **5 steps to working voice chat:**

1. **Setup**: Redeem Cal Hacks code, get credentials (2 min)
2. **CLI**: Install and authenticate (2 min)
3. **Agent**: Create from boilerplate (2 min)
4. **Customize**: Add podcast context (5 min)
5. **iOS**: Add SDK and connect (5 min)

**Total time: ~15 minutes!**

The agent handles all the AI (STT, LLM, TTS) server-side. iOS just streams audio in/out. Simple! 🎉

