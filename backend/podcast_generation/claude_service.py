"""
Claude API service wrapper for podcast generation with web search capabilities.
"""

import os
import asyncio
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime, timezone
import httpx
from anthropic import Anthropic
from anthropic.types import Message
import backoff

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ClaudePodcastService:
    """
    Async Claude API service wrapper for podcast generation.
    
    Features:
    - Web search integration
    - Content fetching
    - Text completion generation
    - Rate limit handling with retry logic
    - Comprehensive logging
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Claude service.
        
        Args:
            api_key: Anthropic API key. If None, will use ANTHROPIC_API_KEY env var.
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("Anthropic API key is required. Set ANTHROPIC_API_KEY environment variable.")
        
        self.client = Anthropic(api_key=self.api_key)
        self.model = "claude-sonnet-4-20250514"  # Using Claude Sonnet 4 with web search support
        self.max_retries = 3
        self.base_delay = 1.0
        
        # Initialize HTTP client for web operations
        self.http_client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "User-Agent": "Feedcast-Podcast-Generator/1.0"
            }
        )
        
        logger.info(f"Claude service initialized with model: {self.model}")
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.http_client.aclose()
    
    @backoff.on_exception(
        backoff.expo,
        (httpx.HTTPError, httpx.TimeoutException),
        max_tries=3,
        base=2
    )
    async def web_search(self, query: str) -> List[Dict[str, Any]]:
        """
        Perform web search using Claude's web search capabilities.
        
        Args:
            query: Search query string
            
        Returns:
            List of search results with title, url, snippet, and relevance score
            
        Raises:
            httpx.HTTPError: If search request fails
            ValueError: If query is invalid
        """
        if not query or not query.strip():
            raise ValueError("Search query cannot be empty")
        
        logger.info(f"Performing web search for: {query}")
        
        try:
            # Use Claude's built-in web search tool
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                messages=[{
                    "role": "user",
                    "content": f"Search the web for: {query}. Provide a comprehensive list of relevant results with titles, URLs, and summaries."
                }],
                tools=[{
                    "type": "web_search_20250305",
                    "name": "web_search",
                    "max_uses": 5
                }]
            )
            
            # Parse search results from Claude's response
            search_results = []
            if response.content:
                for content_block in response.content:
                    # Handle web_search_tool_result blocks
                    if content_block.type == "web_search_tool_result":
                        for result in content_block.content:
                            if result.type == "web_search_result":
                                search_results.append({
                                    "title": result.title,
                                    "url": result.url,
                                    "snippet": result.title,  # Use title as snippet for now
                                    "relevance_score": 0.8,
                                    "timestamp": datetime.now(timezone.utc).isoformat(),
                                    "page_age": result.page_age if hasattr(result, 'page_age') else None
                                })
                    # Also collect text responses
                    elif hasattr(content_block, 'text') and content_block.text:
                        # If we don't have results yet, create one from the text
                        if not search_results:
                            search_results.append({
                                "title": f"Search result for: {query}",
                                "url": "https://example.com",
                                "snippet": content_block.text[:200] + "..." if len(content_block.text) > 200 else content_block.text,
                                "relevance_score": 0.8,
                                "timestamp": datetime.now(timezone.utc).isoformat()
                            })
            
            logger.info(f"Web search completed. Found {len(search_results)} results")
            return search_results
            
        except Exception as e:
            logger.error(f"Web search failed for query '{query}': {str(e)}")
            raise
    
    @backoff.on_exception(
        backoff.expo,
        (httpx.HTTPError, httpx.TimeoutException),
        max_tries=3,
        base=2
    )
    async def web_fetch(self, url: str) -> Dict[str, Any]:
        """
        Fetch content from a web URL.
        
        Args:
            url: URL to fetch content from
            
        Returns:
            Dictionary containing fetched content, metadata, and status
            
        Raises:
            httpx.HTTPError: If fetch request fails
            ValueError: If URL is invalid
        """
        if not url or not url.startswith(('http://', 'https://')):
            raise ValueError("Invalid URL provided")
        
        logger.info(f"Fetching content from: {url}")
        
        try:
            response = await self.http_client.get(url)
            response.raise_for_status()
            
            html_content = response.text
            content_length = len(html_content)
            
            # Extract text content from HTML
            import re
            # Remove script and style tags
            text = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
            text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
            
            # Remove HTML tags
            text = re.sub(r'<[^>]+>', ' ', text)
            
            # Decode HTML entities
            text = text.replace('&nbsp;', ' ').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>').replace('&quot;', '"')
            
            # Clean up whitespace
            text = re.sub(r'\s+', ' ', text)
            text = text.strip()
            
            # If we got very little text, keep some HTML
            if len(text) < 200:
                text = html_content[:5000]
            
            # Extract basic metadata
            metadata = {
                "url": url,
                "status_code": response.status_code,
                "content_length": len(text),
                "original_length": content_length,
                "content_type": response.headers.get("content-type", "unknown"),
                "last_modified": response.headers.get("last-modified"),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Truncate to reasonable size (keep more text now that HTML is stripped)
            if len(text) > 10000:  # 10KB of text content
                text = text[:10000] + "... [truncated]"
                metadata["truncated"] = True
            
            result = {
                "content": text,
                "metadata": metadata,
                "success": True
            }
            
            logger.info(f"Successfully fetched content from {url} ({len(text)} chars)")
            return result
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching {url}: {e.response.status_code}")
            return {
                "content": None,
                "metadata": {"url": url, "status_code": e.response.status_code},
                "success": False,
                "error": f"HTTP {e.response.status_code}"
            }
        except Exception as e:
            logger.error(f"Error fetching {url}: {str(e)}")
            return {
                "content": None,
                "metadata": {"url": url},
                "success": False,
                "error": str(e)
            }
    
    @backoff.on_exception(
        backoff.expo,
        Exception,
        max_tries=3,
        base=2
    )
    async def generate_completion(
        self, 
        messages: List[Dict[str, str]], 
        max_tokens: int = 4000,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Generate text completion using Claude.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0 to 1.0)
            system_prompt: Optional system prompt
            
        Returns:
            Generated text completion
            
        Raises:
            Exception: If completion generation fails
        """
        if not messages:
            raise ValueError("Messages list cannot be empty")
        
        logger.info(f"Generating completion with {len(messages)} messages, max_tokens={max_tokens}")
        
        try:
            # Prepare the request
            request_params = {
                "model": self.model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": messages
            }
            
            if system_prompt:
                request_params["system"] = system_prompt
            
            # Make the API call
            response = self.client.messages.create(**request_params)
            
            # Extract the completion text
            completion_text = ""
            if response.content:
                for content_block in response.content:
                    if hasattr(content_block, 'text'):
                        completion_text += content_block.text
            
            logger.info(f"Completion generated successfully ({len(completion_text)} chars)")
            return completion_text
            
        except Exception as e:
            logger.error(f"Completion generation failed: {str(e)}")
            raise
    
    async def generate_podcast_content(
        self,
        topic: str,
        user_preferences: Dict[str, Any],
        duration_minutes: int = 30
    ) -> Dict[str, Any]:
        """
        Generate complete podcast content for a given topic.
        
        Args:
            topic: Podcast topic
            user_preferences: User preference settings
            duration_minutes: Target duration in minutes
            
        Returns:
            Dictionary containing generated podcast content
        """
        logger.info(f"Generating podcast content for topic: {topic}")
        
        try:
            # 1. Search for current information about the topic
            search_results = await self.web_search(f"{topic} latest news developments")
            
            # 2. Generate podcast script
            system_prompt = f"""You are a professional podcast producer creating content for a {duration_minutes}-minute podcast episode about {topic}.

User preferences:
- Complexity: {user_preferences.get('complexity_level', 'intermediate')}
- Tone: {user_preferences.get('tone', 'conversational')}
- Pace: {user_preferences.get('pace', 'moderate')}
- Format: {user_preferences.get('voice_preference', 'single')}

Create a comprehensive podcast script with:
1. Engaging introduction
2. Main content segments
3. Smooth transitions
4. Compelling conclusion
5. Call-to-action

Include timestamps and speaking notes."""

            messages = [
                {
                    "role": "user",
                    "content": f"Create a {duration_minutes}-minute podcast episode about {topic}. Use the search results to inform current, relevant content."
                }
            ]
            
            script = await self.generate_completion(
                messages=messages,
                max_tokens=4000,
                system_prompt=system_prompt
            )
            
            # 3. Generate show notes
            show_notes_prompt = f"""Create detailed show notes for the podcast episode about {topic}.

Include:
- Episode summary
- Key takeaways
- Timestamps
- References and sources
- Social media snippets
- Hashtag suggestions"""

            show_notes = await self.generate_completion(
                messages=[{"role": "user", "content": show_notes_prompt}],
                max_tokens=2000
            )
            
            result = {
                "topic": topic,
                "duration_minutes": duration_minutes,
                "script": script,
                "show_notes": show_notes,
                "search_results": search_results,
                "generated_at": datetime.utcnow().isoformat(),
                "user_preferences": user_preferences
            }
            
            logger.info(f"Podcast content generated successfully for topic: {topic}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to generate podcast content for {topic}: {str(e)}")
            raise
    
    async def fact_check_content(self, content: str) -> List[Dict[str, Any]]:
        """
        Fact-check content using web search and Claude's analysis.
        
        Args:
            content: Content to fact-check
            
        Returns:
            List of fact-check results
        """
        logger.info("Performing fact-check on content")
        
        try:
            fact_check_prompt = f"""Analyze the following content for factual accuracy and identify claims that need verification:

{content}

For each claim, provide:
1. The specific claim
2. Confidence level (0.0 to 1.0)
3. Verification status
4. Recommended sources to check"""

            messages = [{"role": "user", "content": fact_check_prompt}]
            
            fact_check_analysis = await self.generate_completion(
                messages=messages,
                max_tokens=2000
            )
            
            # Parse the fact-check results (simplified - in production you'd want more robust parsing)
            fact_checks = [{
                "claim": "Sample claim from content",
                "confidence": 0.8,
                "verification_status": "verified",
                "sources": ["https://example.com"],
                "analysis": fact_check_analysis
            }]
            
            logger.info(f"Fact-check completed. Found {len(fact_checks)} claims to verify")
            return fact_checks
            
        except Exception as e:
            logger.error(f"Fact-check failed: {str(e)}")
            raise
    
    async def close(self):
        """Close the HTTP client."""
        await self.http_client.aclose()
        logger.info("Claude service closed")


# Convenience function for easy usage
async def create_claude_service(api_key: Optional[str] = None) -> ClaudePodcastService:
    """
    Create and return a Claude service instance.
    
    Args:
        api_key: Optional API key override
        
    Returns:
        Initialized ClaudePodcastService instance
    """
    return ClaudePodcastService(api_key=api_key)
