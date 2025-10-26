"""
Claude service for chat and search functionality.
"""

import os
from typing import List, Dict, Any, Optional
from anthropic import Anthropic


class ClaudeService:
    """
    Service for interacting with Claude API for chat and reasoning.
    """
    
    def __init__(self):
        """Initialize the Claude service."""
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        self.client = None
        
        if self.api_key:
            try:
                self.client = Anthropic(api_key=self.api_key)
                print("Claude service initialized successfully")
            except Exception as e:
                print(f"Error initializing Claude service: {e}")
        else:
            print("Warning: ANTHROPIC_API_KEY not found in environment variables")
    
    def is_available(self) -> bool:
        """Check if Claude service is available."""
        return self.client is not None
    
    async def generate_response(
        self, 
        message: str, 
        history: List[Dict[str, Any]] = None,
        search_results: Optional[str] = None
    ) -> str:
        """
        Generate a response using Claude.
        
        Args:
            message: The user's current message
            history: Previous conversation history
            search_results: Optional search results to include in context
            
        Returns:
            Claude's response
        """
        if not self.is_available():
            return "I'm sorry, but I'm not available right now. Please check my configuration."
        
        try:
            # Build the conversation context
            messages = []
            
            # Add conversation history
            if history:
                for msg in history:
                    messages.append({
                        "role": msg.get("role", "user"),
                        "content": msg.get("content", "")
                    })
            
            # Add current message
            messages.append({
                "role": "user",
                "content": message
            })
            
            # Build system prompt
            system_prompt = self._build_system_prompt(search_results)
            
            # Make the API call
            response = self.client.messages.create(
                model="claude-3-5-haiku-20241022",
                max_tokens=1000,
                system=system_prompt,
                messages=messages
            )
            
            return response.content[0].text
            
        except Exception as e:
            print(f"Error generating Claude response: {e}")
            return "I apologize, but I encountered an error while processing your request."
    
    def _build_system_prompt(self, search_results: Optional[str] = None) -> str:
        """
        Build the system prompt for Claude.
        
        Args:
            search_results: Optional search results to include
            
        Returns:
            System prompt string
        """
        base_prompt = """You are a helpful AI assistant. You can engage in conversation, answer questions, and provide information based on your knowledge and any search results provided.

Guidelines:
- Be helpful, accurate, and concise
- If search results are provided, use them to inform your response
- If you don't know something, say so rather than guessing
- Maintain a friendly and professional tone
"""
        
        if search_results:
            base_prompt += f"\n\nSearch Results:\n{search_results}\n\nUse these search results to provide accurate, up-to-date information when relevant."
        
        return base_prompt
    
    async def analyze_search_need(self, message: str, history: List[Dict[str, Any]] = None) -> bool:
        """
        Analyze whether a message requires live search.
        
        Args:
            message: The user's message
            history: Previous conversation history
            
        Returns:
            True if search is recommended, False otherwise
        """
        if not self.is_available():
            return False
        
        try:
            analysis_prompt = f"""
Analyze the following user message and determine if it requires live search for current information.

User message: "{message}"

Consider:
- Does the user need current/recent information?
- Are they asking about news, prices, weather, or other time-sensitive data?
- Would your existing knowledge be sufficient?

Respond with only "YES" if live search is needed, or "NO" if not needed.
"""
            
            response = self.client.messages.create(
                model="claude-3-5-haiku-20241022",
                max_tokens=10,
                messages=[{"role": "user", "content": analysis_prompt}]
            )
            
            result = response.content[0].text.strip().upper()
            return result == "YES"
            
        except Exception as e:
            print(f"Error analyzing search need: {e}")
            return False
