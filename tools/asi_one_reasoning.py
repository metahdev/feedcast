"""
LLMReasoner - Advanced Reasoning Engine
Contains the complex LLM orchestration logic for the PACoS Brain
"""

import os
from uagents import Context
from typing import Dict, Any, Tuple
from anthropic import Anthropic
from dotenv import load_dotenv
from .pacos_tools import live_web_search_async, get_user_memory
from .intent_classifier import classify_query_intent

# Load environment variables
load_dotenv()


async def get_llm_response(ctx: Context, user_query: str, memory: Dict[str, Any]) -> Tuple[str, str]:
    """
    ASI:One reasoning engine that orchestrates LLM responses with tool usage.
    
    Uses Anthropic Claude to intelligently process queries and generate optimized search terms.
    
    Args:
        ctx (Context): uAgent context for logging
        user_query (str): The user's query/request
        memory (Dict[str, Any]): User memory and context data
        
    Returns:
        Tuple[str, str]: (response_text, source_metadata)
    """
    
    ctx.logger.info("ASI:One reasoning engine processing query...")
    
    try:
        # Initialize Anthropic client
        anthropic = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        
        # Step 1: Analyze the query and extract search intent
        analysis_prompt = f"""
        Analyze this user query and extract the core search intent for a web search.
        
        User Query: "{user_query}"
        
        Extract the most relevant search terms that would find current, accurate information.        
        Return only the optimized search query, nothing else.
        """
        
        analysis_response = anthropic.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=100,
            messages=[{"role": "user", "content": analysis_prompt}]
        )
        
        optimized_search_query = analysis_response.content[0].text.strip()
        ctx.logger.info(f"ASI:One extracted search intent: {optimized_search_query}")
        
        # Step 2: Use hybrid intent classifier for better accuracy
        intent_result = await classify_query_intent(user_query)
        ctx.logger.info(f"LLMReasoner intent analysis: {intent_result}")
        
        # Extract decision and confidence
        needs_live_data = "YES" if intent_result["decision"] == "LIVE" else "NO"
        confidence = intent_result.get("confidence", 0.5)
        reasoning = intent_result.get("reasoning", "No reasoning provided")
        method = intent_result.get("method", "unknown")
        
        ctx.logger.info(f"Intent decision: {needs_live_data}, confidence: {confidence}, method: {method}")
        ctx.logger.info(f"Reasoning: {reasoning}")
        
        # Use optimized search query for live searches
        search_query = optimized_search_query
        
        # Execute based on Claude's decision
        if needs_live_data == "YES":
            ctx.logger.info(f"LLMReasoner executing live search: {search_query}")
            try:
                tool_result = await live_web_search_async(search_query)
                ctx.logger.info("Live search completed successfully")
            except Exception as e:
                ctx.logger.error(f"Live search failed: {e}")
                tool_result = f"Live search failed: {str(e)}"
        else:
            ctx.logger.info("LLMReasoner using knowledge/memory response")
            tool_result = "Using internal knowledge and user memory"
        
        # Step 3: Use Claude to synthesize the response intelligently
        synthesis_prompt = f"""
        You are LLMReasoner, providing a helpful response to the user.
        
        User Query: "{user_query}"
        Live Data Needed: {needs_live_data}
        Search Query Used: {search_query if needs_live_data == "YES" else "N/A"}
        Tool Result: {tool_result}
        User Interests: {memory.get('interest_scores', {})}
        
        Create a natural, conversational response that:
        1. Directly answers the user's question
        2. Uses the most relevant information available
        3. Is concise and easy to understand
        4. Feels personal based on their interests
        5. Acknowledges the source of information
        
        Keep it under 200 words and be conversational.
        """
        
        synthesis_response = anthropic.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=300,
            messages=[{"role": "user", "content": synthesis_prompt}]
        )
        
        response = synthesis_response.content[0].text.strip()
        source_metadata = f"Intelligent analysis: {needs_live_data} data for query: {search_query if needs_live_data == 'YES' else 'memory-based'}"
        
        return response, source_metadata
            
    except Exception as e:
        ctx.logger.error(f"ASI:One reasoning error: {e}")
        # Intelligent fallback - let Claude decide even in error cases
        try:
            fallback_prompt = f"""
            I encountered an error, but I still want to help the user.
            
            User Query: "{user_query}"
            User Memory: {memory}
            
            Provide a helpful response that acknowledges the error but still tries to help.
            Be honest about the technical issue but remain helpful and conversational.
            """
            
            fallback_response = anthropic.messages.create(
                model="claude-3-5-haiku-20241022",
                max_tokens=200,
                messages=[{"role": "user", "content": fallback_prompt}]
            )
            
            response = fallback_response.content[0].text.strip()
            source_metadata = f"Fallback response due to error: {str(e)}"
            
        except:
            # Final fallback
            response = f"I apologize, but I encountered a technical issue while processing your query: '{user_query}'. Please try again in a moment."
            source_metadata = f"Technical error fallback for query: {user_query}"
        
        return response, source_metadata


