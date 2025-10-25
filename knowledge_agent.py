"""
KnowledgeAgent - MCP Server and Reasoning Engine
The central brain of the PACoS system that processes queries using LLM reasoning
"""

from uagents import Agent, Context
from messages import AgentQuery, AgentResponse
from tools.pacos_tools import get_user_memory
from tools.asi_one_reasoning import get_llm_response

# Initialize the KnowledgeAgent
knowledge_agent = Agent(
    name="KnowledgeAgent",
    seed="knowledge_agent_secret_seed_12345",
    port=8001,
    endpoint=["http://127.0.0.1:8001/submit"]
)

# MCP Tool Registration
# Tools are now imported from tools/pacos_tools.py

# A2A Message Handler with LLM Reasoning
@knowledge_agent.on_message(model=AgentQuery, replies=AgentResponse)
async def handle_agent_query(ctx: Context, sender: str, msg: AgentQuery):
    """
    Handle incoming queries from VoiceClientAgent using LLM reasoning
    """
    ctx.logger.info(f"KnowledgeAgent received query: {msg.user_text}")
    
    # Prevent self-referencing loops
    if sender == knowledge_agent.address:
        ctx.logger.warning("Ignoring self-referencing query to prevent infinite loops")
        return
    
    try:
        # Get user memory data
        user_memory = get_user_memory()
        
        # Use LLM reasoning engine to process the query
        response_text, source_metadata = await get_llm_response(
            ctx=ctx,
            user_query=msg.user_text,
            memory=user_memory
        )
        
        # Create and send response
        response = AgentResponse(
            script=response_text,
            source_metadata=source_metadata
        )
        
        ctx.logger.info(f"KnowledgeAgent sending response to {sender}")
        await ctx.send(sender, response)
        
    except Exception as e:
        ctx.logger.error(f"Error processing query: {e}")
        # Fallback response
        fallback_response = AgentResponse(
            script="I encountered an error processing your request. Please try again.",
            source_metadata="Error handling fallback"
        )
        await ctx.send(sender, fallback_response)

# Startup handler
@knowledge_agent.on_event("startup")
async def startup_handler(ctx: Context):
    ctx.logger.info(f"KnowledgeAgent ({knowledge_agent.name}) is starting up on port 8001")
    ctx.logger.info("LLM reasoning engine initialized")
    ctx.logger.info("MCP tools registered: live_web_search")
    ctx.logger.info("Ready to process queries with advanced reasoning")

if __name__ == "__main__":
    knowledge_agent.run()
