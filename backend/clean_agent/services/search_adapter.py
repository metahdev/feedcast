"""
Search adapter for integrating with live search functionality.
"""

import os
import sys
from typing import Optional, Dict, Any
from pathlib import Path


class SearchAdapter:
    """
    Adapter for integrating with the existing live search tool.
    """
    
    def __init__(self):
        """Initialize the search adapter."""
        self.search_tool = None
        self._initialize_search_tool()
    
    def _initialize_search_tool(self):
        """Initialize the search tool by importing from the existing codebase."""
        try:
            # Add the parent directory to the path to import from the main project
            parent_dir = Path(__file__).parent.parent.parent.parent
            sys.path.insert(0, str(parent_dir))
            
            # Try to import the live search tool
            from tools.live_search_tool import LiveSearchTool
            
            self.search_tool = LiveSearchTool()
            print("Search adapter initialized with live search tool")
            
        except ImportError as e:
            print(f"Warning: Could not import live search tool: {e}")
            print("Search functionality will be limited")
            self.search_tool = None
        except Exception as e:
            print(f"Error initializing search tool: {e}")
            self.search_tool = None
    
    def is_available(self) -> bool:
        """Check if search functionality is available."""
        return self.search_tool is not None
    
    async def search(self, query: str) -> Optional[str]:
        """
        Perform a live search for the given query.
        
        Args:
            query: Search query string
            
        Returns:
            Search results as a formatted string, or None if search failed
        """
        if not self.is_available():
            return "Search functionality is not available."
        
        try:
            # Use the existing search tool
            results = await self.search_tool.cached_search(query)
            
            if not results:
                return "No search results found."
            
            # Format the results for Claude
            formatted_results = self._format_search_results(results)
            return formatted_results
            
        except Exception as e:
            print(f"Error performing search: {e}")
            return f"Search failed: {str(e)}"
    
    def _format_search_results(self, results: Dict[str, Any]) -> str:
        """
        Format search results for inclusion in Claude's context.
        
        Args:
            results: Raw search results
            
        Returns:
            Formatted search results string
        """
        if not results:
            return "No search results found."
        
        formatted = "Search Results:\n\n"
        
        # Handle different result formats
        if isinstance(results, list):
            for i, result in enumerate(results[:5], 1):  # Limit to top 5 results
                if isinstance(result, dict):
                    title = result.get('title', 'No title')
                    snippet = result.get('snippet', result.get('description', 'No description'))
                    url = result.get('url', '')
                    
                    formatted += f"{i}. {title}\n"
                    formatted += f"   {snippet}\n"
                    if url:
                        formatted += f"   URL: {url}\n"
                    formatted += "\n"
                else:
                    formatted += f"{i}. {str(result)}\n\n"
        
        elif isinstance(results, dict):
            # Handle single result or structured data
            if 'title' in results:
                formatted += f"Title: {results.get('title', 'No title')}\n"
                formatted += f"Content: {results.get('snippet', results.get('content', 'No content'))}\n"
                if 'url' in results:
                    formatted += f"URL: {results['url']}\n"
            else:
                # Generic dict formatting
                for key, value in results.items():
                    formatted += f"{key}: {value}\n"
        
        else:
            # Fallback for other types
            formatted += str(results)
        
        return formatted
    
    async def test_search(self) -> bool:
        """
        Test the search functionality.
        
        Returns:
            True if search is working, False otherwise
        """
        if not self.is_available():
            return False
        
        try:
            test_results = await self.search_tool.cached_search("test query")
            return test_results is not None and "Search failed" not in test_results
        except Exception as e:
            print(f"Search test failed: {e}")
            return False
