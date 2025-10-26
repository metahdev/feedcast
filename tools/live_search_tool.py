"""
Live Search Tool for PACoS Brain
--------------------------------
Performs real-time web searches using Tavily and Serper APIs with async caching.
Integrates seamlessly with ASI:One reasoning module.
"""

import aiohttp
import asyncio
import os
from functools import lru_cache
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Environment Variables
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
SERPER_API_KEY = os.getenv("SERPER_API_KEY")


class LiveSearchTool:
    """Async live search tool with Tavily primary and Serper fallback"""
    
    tavily_url = "https://api.tavily.com/search"
    serper_url = "https://google.serper.dev/search"

    @staticmethod
    @lru_cache(maxsize=128)
    async def cached_search(query: str, max_results: int = 5) -> Dict[str, Any]:
        """Cached async wrapper for repeated queries"""
        return await LiveSearchTool._search(query, max_results)

    @staticmethod
    async def _search(query: str, max_results: int = 5) -> Dict[str, Any]:
        """Primary: Tavily → fallback: Serper"""
        result = await LiveSearchTool._tavily_search(query, max_results)
        
        if result is None:
            result = await LiveSearchTool._serper_search(query, max_results)
        
        if result is None:
            return {"error": "All search engines failed."}
        
        return result

    @staticmethod
    async def _tavily_search(query: str, max_results: int) -> Optional[Dict[str, Any]]:
        """Search using Tavily API"""
        if not TAVILY_API_KEY:
            return None
        
        payload = {
            "query": query, 
            "num_results": max_results, 
            "include_answer": True,
            "include_raw_content": True
        }
        headers = {"Authorization": f"Bearer {TAVILY_API_KEY}"}
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    LiveSearchTool.tavily_url, 
                    json=payload, 
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as r:
                    if r.status == 200:
                        data = await r.json()
                        return {
                            "engine": "tavily",
                            "summary": data.get("answer", ""),
                            "results": [
                                {
                                    "title": i["title"], 
                                    "url": i["url"], 
                                    "snippet": i.get("content", ""),
                                    "full_content": i.get("raw_content", "")
                                }
                                for i in data.get("results", [])
                            ],
                        }
                    else:
                        return None
            except Exception as e:
                return None

    @staticmethod
    async def _serper_search(query: str, max_results: int) -> Optional[Dict[str, Any]]:
        """Search using Serper API as fallback"""
        if not SERPER_API_KEY:
            return None
            
        headers = {
            "X-API-KEY": SERPER_API_KEY, 
            "Content-Type": "application/json"
        }
        payload = {"q": query, "num": max_results}
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    LiveSearchTool.serper_url, 
                    json=payload, 
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as r:
                    if r.status == 200:
                        data = await r.json()
                        results = data.get("organic", [])
                        return {
                            "engine": "serper",
                            "summary": results[0]["snippet"] if results else "",
                            "results": [
                                {
                                    "title": i["title"], 
                                    "url": i["link"], 
                                    "snippet": i.get("snippet", "")
                                }
                                for i in results[:max_results]
                            ],
                        }
                    else:
                        return None
            except Exception as e:
                return None

    @staticmethod
    async def refine_live_result(raw: Dict[str, Any]) -> str:
        """Refine raw search data into a coherent, source-backed summary"""
        if not raw or "results" not in raw:
            return "No data available."
        
        top = raw["results"][:3]
        joined = "\n".join([f"- {r['title']} ({r['url']})" for r in top])
        return f"Summary: {raw.get('summary', 'No summary.')}\n\nTop Sources:\n{joined}"


# Test harness
if __name__ == "__main__":
    async def test():
        query = "latest AI news 2024"
        result = await LiveSearchTool.cached_search(query)
        print("Search Results:")
        print(result)

    asyncio.run(test())
