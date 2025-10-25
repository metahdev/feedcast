"""
VoiceClientAgent - A2A Client for Input/Output Handling
Handles query initiation and response reception from users
"""

from uagents import Agent, Context
from messages import AgentQuery, AgentResponse

# Initialize the VoiceClientAgent
voice_client_agent = Agent(
    name="VoiceClientAgent",
    seed="voice_client_agent_secret_seed_67890",
    port=8000,
    endpoint=["http://127.0.0.1:8000/submit"]
)

# Knowledge Agent address - will be set dynamically
KNOWLEDGE_AGENT_ADDRESS = None

# Conversation state to prevent infinite loops
conversation_state = {
    "query_count": 0,
    "max_queries": 3,  # Limit to 3 automatic queries
    "is_active": True
}

# A2A Response Handler
@voice_client_agent.on_message(model=AgentResponse)
async def handle_agent_response(ctx: Context, sender: str, msg: AgentResponse):
    """
    Handle responses from KnowledgeAgent
    """
    global conversation_state
    
    ctx.logger.info("=" * 50)
    ctx.logger.info("RECEIVED RESPONSE FROM KNOWLEDGE AGENT:")
    ctx.logger.info(f"Script: {msg.script}")
    ctx.logger.info(f"Source Metadata: {msg.source_metadata}")
    ctx.logger.info("=" * 50)
    
    # Increment query count and check if we should stop
    conversation_state["query_count"] += 1
    if conversation_state["query_count"] >= conversation_state["max_queries"]:
        conversation_state["is_active"] = False
        ctx.logger.info(f"🛑 Reached maximum queries ({conversation_state['max_queries']}). Stopping automatic queries.")
        ctx.logger.info("💡 To restart, set conversation_state['is_active'] = True")

# A2A Trigger - Simulate query every 10 seconds (with limits)
@voice_client_agent.on_interval(period=10.0)  # Use float instead of timedelta
async def trigger_query(ctx: Context):
    """
    Simulate a query every 10 seconds (limited to prevent infinite loops)
    The test query is designed to force MCP tool call
    """
    global conversation_state
    
    # Check if we should continue sending queries
    if not conversation_state["is_active"]:
        ctx.logger.info("🛑 Conversation inactive. Skipping query.")
        return
    
    if conversation_state["query_count"] >= conversation_state["max_queries"]:
        ctx.logger.info(f"🛑 Maximum queries reached ({conversation_state['max_queries']}). Stopping.")
        return
    
    # Rotate through different test queries
    test_queries = [
        "Hey Chief, what is the current price of gold right now?",
        "What's the latest news about AI regulation?",
        "Tell me about the current stock market trends."
    ]
    
    query_index = conversation_state["query_count"] % len(test_queries)
    test_query = test_queries[query_index]
    
    ctx.logger.info(f"📤 Sending query #{conversation_state['query_count'] + 1} to Knowledge Agent: {test_query}")
    
    # Create the query message
    query = AgentQuery(user_text=test_query)
    
    try:
        # Use the Knowledge Agent address from the startup
        if KNOWLEDGE_AGENT_ADDRESS:
            await ctx.send(KNOWLEDGE_AGENT_ADDRESS, query)
            ctx.logger.info("✅ Query sent successfully")
        else:
            ctx.logger.error("❌ Knowledge Agent address not set")
    except Exception as e:
        ctx.logger.error(f"❌ Failed to send query: {e}")

# Startup handler
@voice_client_agent.on_event("startup")
async def startup_handler(ctx: Context):
    global KNOWLEDGE_AGENT_ADDRESS, conversation_state
    
    ctx.logger.info(f"VoiceClientAgent {voice_client_agent.name} is starting up on port 8000")
    ctx.logger.info("Will send test queries every 10 seconds (limited to 3 queries)")
    ctx.logger.info("Test queries will rotate through different topics")
    ctx.logger.info("Will automatically stop after 3 queries to prevent infinite loops")
    
    # Reset conversation state
    conversation_state["query_count"] = 0
    conversation_state["is_active"] = True
    
    # Set the KnowledgeAgent address - updated with the actual address
    KNOWLEDGE_AGENT_ADDRESS = "agent1qdyhxh77p4p23etzsjq8nxafxwmuv0hqk2ndw4v7qksn9gtcn4rnctle54f"
    ctx.logger.info(f"KnowledgeAgent address set to: {KNOWLEDGE_AGENT_ADDRESS}")

if __name__ == "__main__":
    voice_client_agent.run()
