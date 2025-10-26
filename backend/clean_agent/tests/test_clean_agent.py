"""
Simple test harness for the clean agent.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the parent directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent_core import CleanAgent
from services.supabase_client import SupabaseClient
from services.memory_service import MemoryService
from services.claude_service import ClaudeService
from services.search_adapter import SearchAdapter


class TestCleanAgent:
    """Simple test harness for the clean agent."""
    
    def __init__(self):
        """Initialize the test harness."""
        self.agent = None
        self.test_results = []
    
    async def run_all_tests(self):
        """Run all tests and report results."""
        print("Starting Clean Agent Tests...")
        print("=" * 50)
        
        # Test individual services
        await self.test_supabase_client()
        await self.test_memory_service()
        await self.test_claude_service()
        await self.test_search_adapter()
        
        # Test the main agent
        await self.test_clean_agent()
        
        # Report results
        self.report_results()
    
    async def test_supabase_client(self):
        """Test Supabase client initialization."""
        print("\nTesting Supabase Client...")
        try:
            client = SupabaseClient()
            is_connected = client.is_connected()
            connection_test = await client.test_connection()
            
            self.test_results.append({
                "test": "Supabase Client",
                "status": "PASS" if is_connected else "SKIP",
                "details": f"Connected: {is_connected}, Test: {connection_test}"
            })
            print(f"✓ Supabase Client: {'Connected' if is_connected else 'Not configured'}")
            
        except Exception as e:
            self.test_results.append({
                "test": "Supabase Client",
                "status": "FAIL",
                "details": str(e)
            })
            print(f"✗ Supabase Client: {e}")
    
    async def test_memory_service(self):
        """Test memory service functionality."""
        print("\nTesting Memory Service...")
        try:
            client = SupabaseClient()
            memory_service = MemoryService(client)
            
            # Test storing a message (will fail gracefully if no DB)
            success = await memory_service.store_message("test_user", "user", "Test message")
            
            # Test retrieving messages
            messages = await memory_service.get_recent_messages("test_user", limit=5)
            
            self.test_results.append({
                "test": "Memory Service",
                "status": "PASS",
                "details": f"Store: {success}, Retrieved: {len(messages)} messages"
            })
            print(f"✓ Memory Service: Store={success}, Retrieved={len(messages)} messages")
            
        except Exception as e:
            self.test_results.append({
                "test": "Memory Service",
                "status": "FAIL",
                "details": str(e)
            })
            print(f"✗ Memory Service: {e}")
    
    async def test_claude_service(self):
        """Test Claude service functionality."""
        print("\nTesting Claude Service...")
        try:
            claude_service = ClaudeService()
            is_available = claude_service.is_available()
            
            if is_available:
                # Test a simple response
                response = await claude_service.generate_response("Hello, this is a test.")
                response_length = len(response) if response else 0
                
                self.test_results.append({
                    "test": "Claude Service",
                    "status": "PASS",
                    "details": f"Available: {is_available}, Response length: {response_length}"
                })
                print(f"✓ Claude Service: Available, Response length: {response_length}")
            else:
                self.test_results.append({
                    "test": "Claude Service",
                    "status": "SKIP",
                    "details": "API key not configured"
                })
                print("⚠ Claude Service: Not configured (API key missing)")
            
        except Exception as e:
            self.test_results.append({
                "test": "Claude Service",
                "status": "FAIL",
                "details": str(e)
            })
            print(f"✗ Claude Service: {e}")
    
    async def test_search_adapter(self):
        """Test search adapter functionality."""
        print("\nTesting Search Adapter...")
        try:
            search_adapter = SearchAdapter()
            is_available = search_adapter.is_available()
            
            if is_available:
                # Test search functionality
                test_search = await search_adapter.test_search()
                
                self.test_results.append({
                    "test": "Search Adapter",
                    "status": "PASS" if test_search else "FAIL",
                    "details": f"Available: {is_available}, Test search: {test_search}"
                })
                print(f"✓ Search Adapter: Available, Test search: {test_search}")
            else:
                self.test_results.append({
                    "test": "Search Adapter",
                    "status": "SKIP",
                    "details": "Search tool not available"
                })
                print("⚠ Search Adapter: Not available (search tool not found)")
            
        except Exception as e:
            self.test_results.append({
                "test": "Search Adapter",
                "status": "FAIL",
                "details": str(e)
            })
            print(f"✗ Search Adapter: {e}")
    
    async def test_clean_agent(self):
        """Test the main clean agent."""
        print("\nTesting Clean Agent...")
        try:
            agent = CleanAgent()
            
            # Test basic message processing
            response = await agent.process_message("Hello, this is a test message.")
            
            self.test_results.append({
                "test": "Clean Agent",
                "status": "PASS",
                "details": f"Response generated: {len(response)} characters"
            })
            print(f"✓ Clean Agent: Response generated ({len(response)} characters)")
            
        except Exception as e:
            self.test_results.append({
                "test": "Clean Agent",
                "status": "FAIL",
                "details": str(e)
            })
            print(f"✗ Clean Agent: {e}")
    
    def report_results(self):
        """Report test results summary."""
        print("\n" + "=" * 50)
        print("TEST RESULTS SUMMARY")
        print("=" * 50)
        
        passed = sum(1 for result in self.test_results if result["status"] == "PASS")
        failed = sum(1 for result in self.test_results if result["status"] == "FAIL")
        skipped = sum(1 for result in self.test_results if result["status"] == "SKIP")
        
        print(f"Total Tests: {len(self.test_results)}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Skipped: {skipped}")
        
        print("\nDetailed Results:")
        for result in self.test_results:
            status_icon = "✓" if result["status"] == "PASS" else "✗" if result["status"] == "FAIL" else "⚠"
            print(f"{status_icon} {result['test']}: {result['status']}")
            print(f"  {result['details']}")


async def main():
    """Run the test harness."""
    tester = TestCleanAgent()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
