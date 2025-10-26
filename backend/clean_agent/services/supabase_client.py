"""
Supabase client factory for the clean agent.
"""

import os
from typing import Optional
from supabase import create_client, Client


class SupabaseClient:
    """
    Factory class for creating and managing Supabase client connections.
    """
    
    def __init__(self):
        """Initialize the Supabase client."""
        self._client: Optional[Client] = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the Supabase client with environment variables."""
        url = os.getenv("SUPABASE_URL")
        # Use service key for backend operations to bypass RLS
        key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY")
        
        if not url or not key:
            print("Warning: Supabase credentials not found in environment variables")
            print("Set SUPABASE_URL and SUPABASE_SERVICE_KEY (or SUPABASE_ANON_KEY) to enable database functionality")
            return
        
        try:
            self._client = create_client(url, key)
            print("Supabase client initialized successfully")
        except Exception as e:
            print(f"Error initializing Supabase client: {e}")
            self._client = None
    
    @property
    def client(self) -> Optional[Client]:
        """Get the Supabase client instance."""
        return self._client
    
    def is_connected(self) -> bool:
        """Check if the Supabase client is properly connected."""
        return self._client is not None
    
    async def test_connection(self) -> bool:
        """
        Test the Supabase connection.
        
        Returns:
            True if connection is successful, False otherwise
        """
        if not self._client:
            return False
        
        try:
            # Simple test query
            result = self._client.table("chat_messages").select("id").limit(1).execute()
            return True
        except Exception as e:
            print(f"Supabase connection test failed: {e}")
            return False
