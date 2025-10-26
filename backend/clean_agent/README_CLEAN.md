# Clean Agent

A small, reliable Claude agent that consults Supabase memory and decides whether to run live search.

## Purpose

The Clean Agent is designed to be a simple, maintainable AI assistant that:
- Integrates with Claude for natural language processing
- Stores and retrieves conversation history using Supabase
- Intelligently decides when to perform live searches
- Provides a clean, modular architecture for easy testing and extension

## Architecture

```
backend/clean_agent/
├── agent_core.py          # Main orchestrator
├── app.py                 # Local testing runner
├── services/
│   ├── supabase_client.py # Database connection
│   ├── memory_service.py  # Chat history management
│   ├── claude_service.py  # Claude API integration
│   └── search_adapter.py  # Live search integration
└── tests/
    └── test_clean_agent.py # Test harness
```

## Setup

### Environment Variables

Create a `.env` file in the `backend/clean_agent/` directory with the following variables:

```bash
# Supabase Configuration
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_anon_key

# Claude API Configuration
ANTHROPIC_API_KEY=your_anthropic_api_key
```

### Database Setup

The agent expects a `chat_messages` table in your Supabase database with the following schema:

```sql
CREATE TABLE chat_messages (
    id SERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    role TEXT NOT NULL, -- 'user', 'assistant', or 'system'
    content TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_chat_messages_user_id ON chat_messages(user_id);
CREATE INDEX idx_chat_messages_created_at ON chat_messages(created_at);
```

## Usage

### Running Tests

To test the agent functionality:

```bash
cd backend/clean_agent
python tests/test_clean_agent.py
```

This will run a comprehensive test suite that checks:
- Supabase connection and configuration
- Memory service functionality
- Claude API integration
- Search adapter availability
- End-to-end agent processing

### Local Testing

To run the agent locally for testing:

```bash
cd backend/clean_agent
python app.py
```

### Programmatic Usage

```python
from agent_core import CleanAgent

# Initialize the agent
agent = CleanAgent()

# Process a message
response = await agent.process_message("Hello, how are you?")
print(response)

# Get conversation history
history = await agent.get_conversation_history("user123")

# Clear conversation history
await agent.clear_conversation("user123")
```

## Features

### Memory Management
- Automatic storage of user and assistant messages
- Conversation history retrieval
- User-specific message isolation
- Conversation clearing functionality

### Intelligent Search
- Automatic detection of queries requiring live information
- Integration with existing search tools
- Fallback handling when search is unavailable

### Error Handling
- Graceful degradation when services are unavailable
- Comprehensive error logging
- Fallback responses for failed operations

### Testing
- Comprehensive test suite
- Individual service testing
- End-to-end integration testing
- Clear test result reporting

## Dependencies

The agent requires the following Python packages:
- `anthropic` - Claude API client
- `supabase` - Supabase client
- `asyncio` - Asynchronous operations

## Notes

- The agent is designed to work independently of the main project
- All external dependencies are optional and gracefully handled
- The search adapter attempts to integrate with existing search tools
- Memory service works with or without Supabase connection
- Claude service requires API key for full functionality

## Troubleshooting

### Common Issues

1. **Supabase Connection Failed**
   - Check your `SUPABASE_URL` and `SUPABASE_ANON_KEY`
   - Ensure the database table exists
   - Verify network connectivity

2. **Claude API Errors**
   - Verify your `ANTHROPIC_API_KEY` is correct
   - Check API rate limits and quotas
   - Ensure you have sufficient API credits

3. **Search Not Working**
   - The search adapter requires the existing search tool
   - Check that the main project's search tools are available
   - Search functionality is optional and will gracefully degrade

### Test Results

The test suite provides detailed information about which services are working:
- ✓ PASS: Service is working correctly
- ✗ FAIL: Service has an error that needs fixing
- ⚠ SKIP: Service is not configured (expected for optional services)
