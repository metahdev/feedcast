# How to Test the Agent

## Method 1: Quick Start (Recommended)
```bash
cd feedcast-livekit/feedcast-agent
source .venv/bin/activate
python src/agent.py dev
```

**What you'll see if it works:**
- Connection messages to LiveKit Cloud
- "Looking for participants..." logs
- Agent waits for iOS app to connect

**What you'll see if it fails:**
- Import errors
- Connection errors
- API key errors

## Method 2: Console Test (Talk to it in Terminal)
```bash
cd feedcast-livekit/feedcast-agent
source .venv/bin/activate
python src/agent.py console
```

**This lets you:**
- Speak directly to the agent
- Test voice responses
- See if transcript parsing works
- Quick smoke test

## Method 3: Check Cloud Deployment
Visit: https://cloud.livekit.io/projects/p_feedcast-gdavr142

Look for:
- Active agents
- Recent connection logs
- Agent status

## Method 4: Test from iOS App
1. Start the agent with `python src/agent.py dev`
2. Open iOS app
3. Start a voice chat
4. Check both logs:
   - iOS console: Shows metadata being sent
   - Agent logs: Shows metadata being received

## What to Look For in Logs

### Successful Connection:
```
✅ Connected to LiveKit room
📦 Loaded podcast context: [podcast title]
📝 Parsed transcript: 37 segments
📝 Formatted transcript: 4892 chars
```

### Problems to Watch For:
```
⚠️ No transcript found in metadata
❌ Failed to parse transcript: [error]
```

## Quick Test Checklist
- [ ] Agent starts without errors
- [ ] Connects to LiveKit Cloud
- [ ] Logs show "Looking for participants"
- [ ] iOS app can connect to agent
- [ ] Agent receives podcast context
- [ ] Agent receives and parses transcript
- [ ] Agent can answer questions about the episode

