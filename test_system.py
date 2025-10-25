#!/usr/bin/env python3
"""
PACoS Brain System Test
Tests the intelligent agent system
"""

import sys
import os

def test_imports():
    """Test that all modules can be imported"""
    try:
        import knowledge_agent
        import voice_agent
        import messages
        from tools.pacos_tools import live_web_search, get_user_memory
        from tools.asi_one_reasoning import get_llm_response
        print("✅ All imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_api_keys():
    """Test that API keys are configured"""
    from dotenv import load_dotenv
    load_dotenv()
    
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    google_key = os.getenv("GOOGLE_API_KEY")
    google_cse = os.getenv("GOOGLE_CSE_ID")
    
    if anthropic_key and anthropic_key != "your_anthropic_api_key_here":
        print("✅ Anthropic API key configured")
    else:
        print("⚠️  Anthropic API key not configured")
    
    if google_key and google_key != "your_google_api_key_here":
        print("✅ Google API key configured")
    else:
        print("⚠️  Google API key not configured")
    
    if google_cse and google_cse != "your_google_cse_id_here":
        print("✅ Google CSE ID configured")
    else:
        print("⚠️  Google CSE ID not configured")

def test_web_search():
    """Test Google Custom Search functionality"""
    try:
        from tools.pacos_tools import live_web_search
        result = live_web_search("test query")
        if "LIVE SEARCH RESULT:" in result:
            print("✅ Google Custom Search working")
            return True
        else:
            print("❌ Google Custom Search not working")
            return False
    except Exception as e:
        print(f"❌ Google Custom Search error: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 PACoS Brain System Test")
    print("=" * 30)
    
    print("\n1. Testing imports...")
    imports_ok = test_imports()
    
    print("\n2. Testing API keys...")
    test_api_keys()
    
    print("\n3. Testing web search...")
    search_ok = test_web_search()
    
    print("\n" + "=" * 30)
    if imports_ok and search_ok:
        print("🎉 System ready! Run 'python knowledge_agent.py' and 'python voice_agent.py'")
    else:
        print("⚠️  Some issues found. Check the errors above.")

if __name__ == "__main__":
    main()
