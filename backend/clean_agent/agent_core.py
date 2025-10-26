"""
Main orchestrator for the clean agent.
Handles message processing, memory integration, and search decisions.
"""

import asyncio
from typing import Optional, Dict, Any
from clean_agent.services.supabase_client import SupabaseClient
from clean_agent.services.memory_service import MemoryService
from clean_agent.services.claude_service import ClaudeService
from clean_agent.services.search_adapter import SearchAdapter


class CleanAgent:
    """
    Main orchestrator that coordinates between Claude, Supabase memory, and search.
    """
    
    def __init__(self):
        """Initialize the clean agent with all required services."""
        self.supabase_client = SupabaseClient()
        self.memory_service = MemoryService(self.supabase_client)
        self.claude_service = ClaudeService()
        self.search_adapter = SearchAdapter()
        
    async def process_message(self, message: str, user_id: str = "default") -> str:
        """
        Process a user message through the complete agent pipeline.
        
        Args:
            message: The user's message
            user_id: User identifier for memory storage
            
        Returns:
            The agent's response
        """
        try:
            # Store the user message in memory
            await self.memory_service.store_message(user_id, "user", message)
            
            # Get relevant conversation history
            history = await self.memory_service.get_recent_messages(user_id, limit=10)
            
            # Check if we need to perform a search
            needs_search = await self._should_search(message, history)
            
            # Perform search if needed
            search_results = None
            if needs_search:
                search_results = await self.search_adapter.search(message)
            
            # Generate response using Claude
            response = await self.claude_service.generate_response(
                message=message,
                history=history,
                search_results=search_results
            )
            
            # Store the agent's response in memory
            await self.memory_service.store_message(user_id, "assistant", response)
            
            return response
            
        except Exception as e:
            error_msg = f"Error processing message: {str(e)}"
            print(error_msg)
            return "I apologize, but I encountered an error processing your request."
    
    async def _should_search(self, message: str, history: list) -> bool:
        """
        Determine if the message requires a live search.
        
        Args:
            message: The current user message
            history: Recent conversation history
            
        Returns:
            True if search is needed, False otherwise
        """
        # Simple heuristic: check for keywords that suggest need for current information
        search_keywords = [
            "current", "latest", "recent", "today", "now", "what's happening",
            "news", "update", "price", "weather", "stock", "crypto"
        ]
        
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in search_keywords)
    
    async def get_conversation_history(self, user_id: str, limit: int = 20) -> list:
        """
        Retrieve conversation history for a user.
        
        Args:
            user_id: User identifier
            limit: Maximum number of messages to retrieve
            
        Returns:
            List of conversation messages
        """
        return await self.memory_service.get_recent_messages(user_id, limit)
    
    async def clear_conversation(self, user_id: str) -> bool:
        """
        Clear conversation history for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            True if successful, False otherwise
        """
        return await self.memory_service.clear_user_messages(user_id)
