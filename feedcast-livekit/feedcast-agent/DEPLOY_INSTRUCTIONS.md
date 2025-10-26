# How to Update the LiveKit Agent

## Current Situation
- **Cloud Agent**: Running old code (deployed hours ago)
- **Your Changes**: New transcript parsing code
- **Issue**: iOS app connects to cloud agent, not your local changes

## Option 1: Deploy to Cloud (Recommended)

```bash
cd feedcast-livekit/feedcast-agent
source .venv/bin/activate

# Deploy updated agent to cloud
python src/agent.py deploy
```

This will:
- Upload your new agent.py code to LiveKit Cloud
- Replace the old agent (CA_GAmszdjdUVR4)
- Your iOS app will automatically use the new code

## Option 2: Run Locally for Testing

```bash
cd feedcast-livekit/feedcast-agent
source .venv/bin/activate

# Run local dev agent
python src/agent.py dev
```

Then modify `feedcast/Config.swift` to use localhost:

```swift
static let liveKitHardcodedToken: String? = "your-local-token"
static let liveKitURL = "ws://localhost:7880"
```

## What Happens Now?

Your iOS app currently connects to:
```
wss://feedcast-gdavr142.livekit.cloud → Cloud Agent (OLD)
```

After deployment, it connects to:
```
wss://feedcast-gdavr142.livekit.cloud → Cloud Agent (NEW with fixes)
```

## Checking Agent Status

Visit: https://cloud.livekit.io/projects/p_feedcast-gdavr142

Look for:
- Active agent: CA_GAmszdjdUVR4
- Last deployed timestamp
- Current status (running/stopped)

