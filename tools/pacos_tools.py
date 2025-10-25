"""
PACoS Brain Tools
Core tool functions for the Knowledge Agent
"""

import os
from dotenv import load_dotenv
from .live_search_tool import LiveSearchTool

# Load environment variables
load_dotenv()


async def live_web_search_async(query: str) -> str:
    """
    Perform async live web search using Tavily/Serper APIs.
    
    Args:
        query (str): The search query string
        
    Returns:
        str: Formatted search results
    """
    try:
        result = await LiveSearchTool.cached_search(query, max_results=5)
        
        if "error" in result:
            return f"LIVE SEARCH RESULT: {result['error']}"
        
        # Format the results for ASI:One
        if result.get("results"):
            formatted_results = []
            for item in result["results"]:
                title = item.get("title", "No Title")
                snippet = item.get("snippet", "No Description")
                full_content = item.get("full_content", "")
                url = item.get("url", "")
                
                # Use full content if available, otherwise use snippet
                content_to_use = full_content if full_content else snippet
                formatted_results.append(f"{title}\n{content_to_use}\nSource: {url}")
            
            summary = result.get("summary", "")
            if summary:
                return f"LIVE SEARCH RESULT: {summary}\n\n---\n" + "\n---\n".join(formatted_results)
            else:
                return "LIVE SEARCH RESULT: " + "\n---\n".join(formatted_results)
        else:
            return f"LIVE SEARCH RESULT: No results found for query: '{query}'"
            
    except Exception as e:
        return f"LIVE SEARCH RESULT: Error occurred while searching for '{query}': {str(e)}"


def get_user_memory() -> dict:
    """
    Retrieve user memory data (simulated Supabase data).
    
    Returns:
        dict: User memory with interest scores and preferences
    """
    return {
        "interest_scores": {
            "tech": 5,
            "finance": 2,
            "science": 4,
            "politics": 3
        },
        "user_preferences": {
            "language": "english",
            "detail_level": "medium"
        }
    }
