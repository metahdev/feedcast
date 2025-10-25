#!/usr/bin/env python3
"""
PACoS Brain Setup Script
Creates .env file with API key placeholders
"""

import os

def create_env_file():
    """Create .env file with API key placeholders"""
    env_content = """# PACoS Brain Environment Variables
# Fill in your actual API keys

# Anthropic Claude API Key (for ASI:One reasoning)
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Google Custom Search Engine API Keys
GOOGLE_API_KEY=your_google_api_key_here
GOOGLE_CSE_ID=your_google_cse_id_here
"""
    
    if not os.path.exists('.env'):
        with open('.env', 'w') as f:
            f.write(env_content)
        print("✅ Created .env file with API key placeholders")
        print("📝 Please edit .env and add your actual API keys")
    else:
        print("⚠️  .env file already exists")

if __name__ == "__main__":
    create_env_file()
