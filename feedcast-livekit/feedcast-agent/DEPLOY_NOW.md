# Deploy the Updated Agent Now

## Current Status
- ✅ iOS code updated (sends transcript via data channel)
- ✅ Agent code updated (reads from data channel)
- ❌ Cloud agent still running OLD code (only reads metadata)

## To Deploy

```bash
cd /Users/metah/Desktop/feedcast/feedcast-livekit/feedcast-agent
source .venv/bin/activate
python src/agent.py deploy
```

## What Will Happen

**Before deployment:**
- Cloud agent receives title ✅ (small, fits in metadata)
- Cloud agent DOESN'T receive transcript ❌ (too large, truncated)
- Cloud agent has no data channel handler

**After deployment:**
- Cloud agent receives title ✅ (small, fits in metadata)
- Cloud agent receives transcript via data channel ✅ (bypasses size limit)
- Cloud agent parses and uses transcript ✅

## Quick Command

```bash
cd feedcast-livekit/feedcast-agent && source .venv/bin/activate && python src/agent.py deploy
```

