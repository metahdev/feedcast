"""
Memory service for storing and retrieving chat messages using Supabase.
"""

import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional
from .supabase_client import SupabaseClient


class MemoryService:
    """
    Service for managing chat message storage and retrieval.
    """
    
    def __init__(self, supabase_client: SupabaseClient):
        """
        Initialize the memory service.
        
        Args:
            supabase_client: Initialized Supabase client
        """
        self.supabase_client = supabase_client
        self.table_name = "chat_messages"
    
    async def store_message(self, user_id: str, role: str, content: str) -> bool:
        """
        Store a chat message in the database.
        
        Args:
            user_id: User identifier
            role: Message role (user, assistant, system)
            content: Message content
            
        Returns:
            True if successful, False otherwise
        """
        if not self.supabase_client.is_connected():
            print("Warning: Supabase not connected, message not stored")
            return False
        
        try:
            message_data = {
                "user_id": user_id,
                "role": role,
                "content": content,
                "created_at": datetime.utcnow().isoformat()
            }
            
            result = self.supabase_client.client.table(self.table_name).insert(message_data).execute()
            return True
            
        except Exception as e:
            print(f"Error storing message: {e}")
            return False
    
    async def get_recent_messages(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Retrieve recent messages for a user.
        
        Args:
            user_id: User identifier
            limit: Maximum number of messages to retrieve
            
        Returns:
            List of message dictionaries
        """
        if not self.supabase_client.is_connected():
            print("Warning: Supabase not connected, returning empty history")
            return []
        
        try:
            result = (
                self.supabase_client.client
                .table(self.table_name)
                .select("*")
                .eq("user_id", user_id)
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )
            
            # Reverse to get chronological order
            messages = result.data[::-1] if result.data else []
            return messages
            
        except Exception as e:
            print(f"Error retrieving messages: {e}")
            return []
    
    async def clear_user_messages(self, user_id: str) -> bool:
        """
        Clear all messages for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            True if successful, False otherwise
        """
        if not self.supabase_client.is_connected():
            print("Warning: Supabase not connected, cannot clear messages")
            return False
        
        try:
            result = (
                self.supabase_client.client
                .table(self.table_name)
                .delete()
                .eq("user_id", user_id)
                .execute()
            )
            return True
            
        except Exception as e:
            print(f"Error clearing messages: {e}")
            return False
    
    async def get_message_count(self, user_id: str) -> int:
        """
        Get the total number of messages for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            Number of messages
        """
        if not self.supabase_client.is_connected():
            return 0
        
        try:
            result = (
                self.supabase_client.client
                .table(self.table_name)
                .select("id", count="exact")
                .eq("user_id", user_id)
                .execute()
            )
            return result.count or 0
            
        except Exception as e:
            print(f"Error getting message count: {e}")
            return 0
