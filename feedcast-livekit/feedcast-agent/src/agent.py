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
            transcript = podcast_context.get("episode_transcript", "")
            
            context_addendum = f"""

CURRENT PODCAST CONTEXT:
- Podcast: "{title}"
- Description: {description}
- Topics: {interests}
- Current Episode: "{episode}"
- Episode Description: {episode_description}

The user is specifically discussing this podcast. Reference these details naturally in your responses and ask relevant questions about the content."""
            
            # Add transcript if available
            if transcript:
                # Truncate if too long (keep first ~3000 chars for context)
                if len(transcript) > 3000:
                    transcript = transcript[:3000] + "\n... (transcript continues)"
                
                context_addendum += f"""

EPISODE TRANSCRIPT:
The following is the full transcript of the episode the user is listening to. Use this to answer specific questions about what was said, discussed, or mentioned in the episode.

{transcript}

When the user asks about specific content, quotes, or topics from the episode, reference this transcript to provide accurate, specific answers."""
            
            instructions = base_instructions + context_addendum
        else:
            instructions = base_instructions
        
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
    
    # Wait a moment for participants to join
    import asyncio
    await asyncio.sleep(0.5)
    
    # Look for user participant and extract metadata
    for participant in ctx.room.remote_participants.values():
        if participant.metadata:
            try:
                import json
                metadata = json.loads(participant.metadata)
                if "podcast_title" in metadata:
                    podcast_context = metadata
                    logger.info(f"📦 Loaded podcast context: {metadata.get('podcast_title')}")
                    
                    # Log transcript availability
                    if "episode_transcript" in metadata:
                        transcript_len = len(metadata.get("episode_transcript", ""))
                        logger.info(f"📝 Transcript available: {transcript_len} characters")
                    else:
                        logger.info("⚠️ No transcript found in metadata")
                    
                    break
            except json.JSONDecodeError:
                logger.warning("Failed to parse participant metadata")
    
    # Also listen for transcript via data channel
    @ctx.room.on("data_received")
    def on_data_received(data_packet):
        try:
            import json
            data = json.loads(data_packet.data.decode('utf-8'))
            if data.get("type") == "podcast_transcript":
                logger.info(f"📤 Received transcript via data channel: {len(data.get('segments', []))} segments")
                if not podcast_context:
                    podcast_context = {}
                # Convert segments back to formatted transcript
                segments = data.get("segments", [])
                transcript_text = "\n".join([f"[{int(s['startTime']//60)}:{int(s['startTime']%60):02d}] {s['text']}" for s in segments])
                podcast_context["episode_transcript"] = transcript_text
        except Exception as e:
            logger.error(f"Failed to process data channel message: {e}")
    
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

    # To use a realtime model instead of a voice pipeline, use the following session setup instead.
    # (Note: This is for the OpenAI Realtime API. For other providers, see https://docs.livekit.io/agents/models/realtime/))
    # 1. Install livekit-agents[openai]
    # 2. Set OPENAI_API_KEY in .env.local
    # 3. Add `from livekit.plugins import openai` to the top of this file
    # 4. Use the following session setup instead of the version above
    # session = AgentSession(
    #     llm=openai.realtime.RealtimeModel(voice="marin")
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
    )


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm))
