"""
Feedcast Podcast Assistant Agent

A voice AI agent specialized in discussing podcasts with users.
Provides engaging conversations about podcast content, episodes, and topics.
"""

import logging

from dotenv import load_dotenv
from livekit.agents import (
    Agent,
    AgentSession,
    JobContext,
    JobProcess,
    MetricsCollectedEvent,
    RoomInputOptions,
    RoomOutputOptions,
    WorkerOptions,
    cli,
    metrics,
)
from livekit.plugins import noise_cancellation, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

logger = logging.getLogger("agent")

load_dotenv(".env.local")


class PodcastAssistant(Agent):
    def __init__(self, podcast_context: dict = None) -> None:
        # Build instructions with podcast context
        base_instructions = """You are an enthusiastic and knowledgeable AI assistant for Feedcast, a podcast discussion app.

Your role is to have natural voice conversations about podcasts. Help users:
- Explore and understand podcast episode content
- Discuss interesting topics and themes from episodes
- Discover new perspectives and insights
- Think critically about what they're listening to

Guidelines:
- Keep responses to 2-3 sentences for natural conversation flow
- Be conversational and friendly, like a fellow podcast enthusiast
- Ask follow-up questions to deepen the discussion
- Avoid complex formatting, emojis, asterisks, or special symbols
- When users mention specific podcasts or episodes, engage with specific details
- If you don't know something about a podcast, be honest and ask them to share more

Remember: This is a voice conversation, so speak naturally and keep it engaging!"""

        # Add podcast-specific context if available
        if podcast_context:
            title = podcast_context.get("podcast_title", "Unknown")
            description = podcast_context.get("podcast_description", "")
            interests = podcast_context.get("podcast_interests", "")
            episode = podcast_context.get("current_episode", "")
            episode_description = podcast_context.get("episode_description", "")
            transcript_json = podcast_context.get("episode_transcript", "")
            
            logger.info(f"🤖 Initializing PodcastAssistant with context:")
            logger.info(f"   Title: {title}")
            logger.info(f"   Episode: {episode}")
            logger.info(f"   Transcript JSON length: {len(transcript_json)} chars")
            
            context_addendum = f"""

CURRENT PODCAST CONTEXT:
- Podcast: "{title}"
- Description: {description}
- Topics: {interests}
- Current Episode: "{episode}"
- Episode Description: {episode_description}

The user is specifically discussing this podcast. Reference these details naturally in your responses and ask relevant questions about the content."""
            
            # Parse and format transcript if available
            transcript = ""
            if transcript_json:
                try:
                    import json
                    # Parse JSON array of segments
                    segments = json.loads(transcript_json)
                    logger.info(f"📝 Parsed transcript: {len(segments)} segments")
                    
                    # Format with timestamps
                    formatted_lines = []
                    for segment in segments:
                        start_time = segment.get("startTime", 0)
                        text = segment.get("text", "")
                        minutes = int(start_time // 60)
                        seconds = int(start_time % 60)
                        formatted_lines.append(f"[{minutes}:{seconds:02d}] {text}")
                    
                    transcript = "\n".join(formatted_lines)
                    logger.info(f"📝 Formatted transcript: {len(transcript)} chars")
                    
                    # Add to context
                    context_addendum += f"""

EPISODE TRANSCRIPT:
The following is the full transcript of the episode the user is listening to. Use this to answer specific questions about what was said, discussed, or mentioned in the episode.

{transcript}

When the user asks about specific content, quotes, or topics from the episode, reference this transcript to provide accurate, specific answers."""
                except Exception as e:
                    logger.error(f"⚠️ Failed to parse transcript: {e}")
                    logger.info(f"📝 Raw transcript: {transcript_json[:200]}...")
            else:
                logger.info("⚠️ No transcript found in podcast context")
            
            instructions = base_instructions + context_addendum
            logger.info(f"📝 Final instructions length: {len(instructions)} chars")
        else:
            instructions = base_instructions
            logger.info("⚠️ No podcast context provided, using generic instructions")
        
        super().__init__(instructions=instructions)

    # To add tools, use the @function_tool decorator.
    # Here's an example that adds a simple weather tool.
    # You also have to add `from livekit.agents import function_tool, RunContext` to the top of this file
    # @function_tool
    # async def lookup_weather(self, context: RunContext, location: str):
    #     """Use this tool to look up current weather information in the given location.
    #
    #     If the location is not supported by the weather service, the tool will indicate this. You must tell the user the location's weather is unavailable.
    #
    #     Args:
    #         location: The location to look up weather information for (e.g. city name)
    #     """
    #
    #     logger.info(f"Looking up weather for {location}")
    #
    #     return "sunny with a temperature of 70 degrees."


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


async def entrypoint(ctx: JobContext):
    # Logging setup
    # Add any other context you want in all log entries here
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }
    
    # Extract podcast context from participant metadata
    podcast_context = None
    await ctx.connect()
    
    # Wait a bit for participants to join
    import asyncio
    await asyncio.sleep(1.0)
    
    # Look for user participant and extract metadata
    # Check all participants (remote and local)
    all_participants = list(ctx.room.remote_participants.values())
    if ctx.room.local_participant:
        all_participants.append(ctx.room.local_participant)
    
    logger.info(f"Looking for participants with metadata. Found {len(all_participants)} participants")
    
    for participant in all_participants:
        if participant.metadata:
            try:
                import json
                metadata = json.loads(participant.metadata)
                logger.info(f"Found metadata for participant {participant.identity}: {metadata.keys()}")
                
                # Log ENTIRE metadata for debugging
                logger.info(f"🔍 Full metadata: {json.dumps(metadata, indent=2)[:500]}")  # First 500 chars
                
                if "podcast_title" in metadata:
                    podcast_context = metadata
                    logger.info(f"📦 Loaded podcast context: {metadata.get('podcast_title')}")
                    logger.info(f"📦 Episode: {metadata.get('current_episode', 'N/A')}")
                    
                    # Log transcript availability
                    transcript = metadata.get("episode_transcript", "")
                    if transcript:
                        logger.info(f"📝 Transcript available: {len(transcript)} characters")
                        
                        # Log a sample of the transcript
                        sample = transcript[:200]
                        logger.info(f"📝 Transcript sample: {sample}...")
                    else:
                        logger.info("⚠️ No transcript found in metadata")
                        logger.info(f"📋 Metadata keys available: {list(metadata.keys())}")
                    
                    break
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse participant metadata for {participant.identity}: {e}")
                logger.warning(f"Raw metadata: {participant.metadata[:200]}")
    
    # Storage for data channel transcript
    transcript_received = {"data": None}
    
    # Listen for data channel messages (for transcript)
    @ctx.room.on("data_received")
    def on_data_received(data_packet):
        logger.info(f"📥 Received data via data channel")
        try:
            import json
            # Try to decode as JSON (the transcript)
            transcript_json = data_packet.data.decode('utf-8')
            logger.info(f"📝 Received transcript via data channel: {len(transcript_json)} chars")
            
            # Store transcript
            transcript_received["data"] = transcript_json
            podcast_context["episode_transcript"] = transcript_json
            logger.info(f"✅ Transcript stored in context")
            
            # Log a sample
            sample = transcript_json[:200]
            logger.info(f"📝 Transcript sample: {sample}...")
            
        except Exception as e:
            logger.error(f"⚠️ Failed to process data channel message: {e}")
    
    # Also listen for new participants or metadata updates
    @ctx.room.on("participant_connected")
    def on_participant_connected(participant):
        logger.info(f"📱 New participant connected: {participant.identity}")
        if participant.metadata:
            try:
                import json
                metadata = json.loads(participant.metadata)
                if "podcast_title" in metadata:
                    logger.info(f"📦 Received podcast context from new participant: {metadata.get('podcast_title')}")
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse new participant metadata: {e}")
    
    # Wait a bit for data channel transcript to arrive
    await asyncio.sleep(0.5)
    
    # Check if transcript was received via data channel
    if podcast_context and not podcast_context.get("episode_transcript") and transcript_received["data"]:
        logger.info("📝 Adding transcript from data channel to context")
        podcast_context["episode_transcript"] = transcript_received["data"]
    
    if not podcast_context:
        logger.info("ℹ️ No podcast context found, using generic assistant")

    # Set up a voice AI pipeline using OpenAI, Cartesia, AssemblyAI, and the LiveKit turn detector
    session = AgentSession(
        # Speech-to-text (STT) is your agent's ears, turning the user's speech into text that the LLM can understand
        # See all available models at https://docs.livekit.io/agents/models/stt/
        stt="assemblyai/universal-streaming:en",
        # A Large Language Model (LLM) is your agent's brain, processing user input and generating a response
        # See all available models at https://docs.livekit.io/agents/models/llm/
        llm="openai/gpt-4.1-mini",
        # Text-to-speech (TTS) is your agent's voice, turning the LLM's text into speech that the user can hear
        # See all available models as well as voice selections at https://docs.livekit.io/agents/models/tts/
        tts="cartesia/sonic-2:9626c31c-bec5-4cca-baa8-f8ba9e84c8bc",
        # VAD and turn detection are used to determine when the user is speaking and when the agent should respond
        # See more at https://docs.livekit.io/agents/build/turns
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        # allow the LLM to generate a response while waiting for the end of turn
        # See more at https://docs.livekit.io/agents/build/audio/#preemptive-generation
        preemptive_generation=True,
    )

    # To get transcriptions for BOTH user AND agent speech, use OpenAI Realtime API instead.
    # Benefits: Agent speech is transcribed too, so users can see both sides of the conversation
    # Steps to enable:
    # 1. Install: pip install 'livekit-agents[openai]'
    # 2. Set OPENAI_API_KEY in .env.local
    # 3. Uncomment the import at the top: `from livekit.plugins import openai`
    # 4. Replace the session setup above with this:
    # session = AgentSession(
    #     llm=openai.realtime.RealtimeModel(voice="marin")  # or "ember", "crimson", "sage", etc.
    # )

    # Metrics collection, to measure pipeline performance
    # For more information, see https://docs.livekit.io/agents/build/metrics/
    usage_collector = metrics.UsageCollector()

    @session.on("metrics_collected")
    def _on_metrics_collected(ev: MetricsCollectedEvent):
        metrics.log_metrics(ev.metrics)
        usage_collector.collect(ev.metrics)

    async def log_usage():
        summary = usage_collector.get_summary()
        logger.info(f"Usage: {summary}")

    ctx.add_shutdown_callback(log_usage)

    # # Add a virtual avatar to the session, if desired
    # # For other providers, see https://docs.livekit.io/agents/models/avatar/
    # avatar = hedra.AvatarSession(
    #   avatar_id="...",  # See https://docs.livekit.io/agents/models/avatar/plugins/hedra
    # )
    # # Start the avatar and wait for it to join
    # await avatar.start(session, room=ctx.room)

    # Start the session, which initializes the voice pipeline and warms up the models
    await session.start(
        agent=PodcastAssistant(podcast_context=podcast_context),
        room=ctx.room,
        room_input_options=RoomInputOptions(
            # For telephony applications, use `BVCTelephony` for best results
            noise_cancellation=noise_cancellation.BVC(),
        ),
        room_output_options=RoomOutputOptions(
            # Enable transcriptions so agent speech appears in the UI
            transcription_enabled=True,
        ),
    )


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm))
