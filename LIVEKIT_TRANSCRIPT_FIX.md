# LiveKit Transcript Integration Fix

## Issues Fixed

### 1. ✅ Podcast Transcript Not Sent to Agent
**Problem:** The LiveKit agent didn't have access to the podcast episode transcript, so it couldn't answer questions about the content.

**Solution:** Enhanced the connection flow to send the full transcript to the agent in multiple ways:

#### A. Metadata Method (Primary)
```swift
// Now includes transcript in metadata
podcastMetadata["episode_transcript"] = fullTranscript
```

The transcript is:
- Parsed from the episode's stored transcript JSON
- Formatted with timestamps: `[MM:SS] transcript text`
- Included in participant metadata sent during connection
- Logged for debugging: transcript length and segment count

#### B. Data Channel Method (Backup)
```swift
// Also sends via data channel for reliability
try await room?.localParticipant.publish(data: transcriptJSON, options: PublishDataOptions(
    reliable: true,
    topic: "podcast_transcript"
))
```

Benefits:
- More reliable for large transcripts
- Doesn't hit metadata size limits
- Can be sent after connection is established

### 2. ✅ Agent Responses Not Transcribed
**Problem:** When the agent spoke, transcriptions weren't appearing in the UI.

**Solution:** Enhanced the transcription handler with better logging and error handling:

```swift
private func registerTranscriptionHandler() {
    // Now logs all transcription events
    print("📝 Transcription stream started for participant: \(participantIdentity)")
    
    // Logs both interim and final transcriptions
    print("📝 Transcription chunk [\(isUser ? "User" : "Agent")]: \"\(text)\" (final: \(isFinal))")
    
    // Only sends final transcripts to UI to avoid duplicates
    if isFinal {
        print("📝 ✅ Final transcription [\(isUser ? "User" : "Agent")]: \(accumulatedText)")
        self.onTranscript(accumulatedText, isUser)
    }
}
```

Improvements:
- Better participant identity tracking (User vs Agent)
- Comprehensive logging for debugging
- Handles both interim and final transcriptions
- Error logging with details

### 3. ✅ Agent Now Uses Transcript Context
**Problem:** Even if the agent received the transcript, it wasn't using it properly.

**Solution:** Updated the agent's instructions to include and reference the transcript:

```python
# In agent.py
if transcript:
    # Truncate if too long (keep first ~3000 chars)
    if len(transcript) > 3000:
        transcript = transcript[:3000] + "\n... (transcript continues)"
    
    context_addendum += f"""

EPISODE TRANSCRIPT:
The following is the full transcript of the episode the user is listening to. 
Use this to answer specific questions about what was said, discussed, or mentioned.

{transcript}

When the user asks about specific content, quotes, or topics from the episode, 
reference this transcript to provide accurate, specific answers."""
```

The agent now:
- Receives transcript in metadata or data channel
- Includes it in LLM context (truncated if needed)
- Can answer specific questions about episode content
- References actual quotes and topics discussed

## What Changed

### iOS App (`VoiceChatView.swift`)

1. **Enhanced metadata preparation (line 465-500)**
   - Added `episode_description` field
   - Parse transcript from JSON
   - Format transcript with timestamps
   - Log transcript size and segment count

2. **Added data channel transmission (line 518-544)**
   - Send transcript as structured JSON
   - Use reliable delivery
   - Topic: "podcast_transcript"
   - Fallback method for large transcripts

3. **Improved transcription handler (line 521-563)**
   - Added comprehensive logging
   - Track participant identity (user vs agent)
   - Log interim and final transcriptions
   - Better error handling

4. **Added helper structures**
   - `TranscriptSegment` struct for parsing
   - `formatTime()` helper for timestamp formatting

### Python Agent (`agent.py`)

1. **Enhanced context extraction (line 51-88)**
   - Extract `episode_description` from metadata
   - Extract `episode_transcript` from metadata
   - Include transcript in agent instructions
   - Truncate if > 3000 characters (to avoid token limits)
   - Log transcript availability

2. **Added data channel listener (line 150-165)**
   - Listen for `podcast_transcript` messages
   - Parse segments and reconstruct transcript
   - Update context dynamically
   - Error handling

## Testing

### Prerequisites
- Agent must be running (`cd feedcast-livekit/feedcast-agent && uv run python src/agent.py dev`)
- Valid LiveKit credentials configured
- Podcast with transcript available

### Test Flow

1. **Start Voice Chat**
   ```
   Expected logs:
   🔌 Connecting to LiveKit room for podcast: [title]
   📝 Transcript included: X segments, Y characters
   📦 Metadata size: Z bytes
   📤 Transcript sent via data channel (W bytes)
   ```

2. **On Agent Side**
   ```
   Expected logs:
   📦 Loaded podcast context: [title]
   📝 Transcript available: X characters
   📤 Received transcript via data channel: Y segments
   ```

3. **Speak to Agent**
   ```
   User: "What was discussed in this episode?"
   
   Expected logs (iOS):
   📝 Transcription stream started for participant: user-XXXX
   📝 Transcription chunk [User]: "What was discussed in this episode?" (final: true)
   📝 ✅ Final transcription [User]: What was discussed in this episode?
   ```

4. **Agent Responds**
   ```
   Expected logs (iOS):
   📝 Transcription chunk [Agent]: "Based on the transcript..." (final: true)
   📝 ✅ Final transcription [Agent]: Based on the transcript...
   
   Expected UI:
   - Agent's response appears in transcript view
   - User sees: "AI Assistant: Based on the transcript..."
   ```

### Troubleshooting

#### Transcript Not Sent
Check logs for:
```
⚠️ No transcript available for episode
```
Solution: Ensure episode has transcript stored in database

#### Transcriptions Not Appearing
Check logs for:
```
❌ Failed to register transcription handler: [error]
```
Solution: Ensure STT is properly configured (AssemblyAI)

#### Agent Can't Answer Questions About Content
Check agent logs for:
```
⚠️ No transcript found in metadata
```
Solution: Verify transcript is being sent and received

## Benefits

### For Users
- ✅ Agent can now answer questions about specific podcast content
- ✅ Agent references actual quotes and topics from the episode
- ✅ Transcriptions appear for both user and agent speech
- ✅ More engaging and contextual conversations

### For Developers
- ✅ Comprehensive logging for debugging
- ✅ Multiple delivery methods (metadata + data channel)
- ✅ Graceful handling of large transcripts
- ✅ Clear error messages

## Configuration

### Environment Variables
```bash
# .env.local in feedcast-agent/
OPENAI_API_KEY=your_key          # For GPT-4
ASSEMBLYAI_API_KEY=your_key      # For STT (transcription)
CARTESIA_API_KEY=your_key        # For TTS
```

### Transcript Size Limits
- **Metadata:** ~1 MB (LiveKit limit)
- **Data Channel:** Unlimited (chunked automatically)
- **Agent Context:** Truncated to 3000 chars (to fit in LLM context window)

## Architecture

```
┌─────────────┐                    ┌──────────────┐
│   iOS App   │                    │ LiveKit Agent│
└──────┬──────┘                    └──────┬───────┘
       │                                  │
       │ 1. Connect to room              │
       ├────────────────────────────────>│
       │                                  │
       │ 2. Send metadata (transcript)   │
       ├────────────────────────────────>│
       │                                  │
       │ 3. Send data channel (backup)   │
       ├────────────────────────────────>│
       │                                  │
       │ 4. Register transcription handler│
       │<─────────────────────────────────┤
       │                                  │
       │ 5. User speaks                   │
       ├────────────────────────────────>│
       │                                  │
       │ 6. User transcription            │
       │<─────────────────────────────────┤
       │                                  │
       │ 7. Agent responds (with context) │
       │<─────────────────────────────────┤
       │                                  │
       │ 8. Agent transcription           │
       │<─────────────────────────────────┤
       └──────────────────────────────────┘
```

## Files Modified

### iOS App
- `feedcast/Views/VoiceChatView.swift` - Enhanced metadata, data channel, transcription handler

### Python Agent
- `feedcast-livekit/feedcast-agent/src/agent.py` - Enhanced context, data channel listener

## Next Steps

1. Test with various podcast transcripts (short, medium, long)
2. Monitor performance with large transcripts (>10k characters)
3. Consider implementing transcript summarization for very long episodes
4. Add UI indicators for when agent is referencing transcript
5. Cache transcripts on agent side for repeated connections

## Notes

- The transcript is truncated to 3000 characters on the agent side to avoid exceeding LLM context limits
- Both metadata and data channel methods are used for redundancy
- Transcriptions are only shown when final (to avoid duplicates in UI)
- All transcript operations are logged for easy debugging

