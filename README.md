# PACoS Brain - Intelligent Agent System

A two-agent system demonstrating Agent-to-Agent (A2A) communication and intelligent tool usage using the Fetch.ai uAgent framework.

## 🧠 System Architecture

### Agents
- **PACoS Brain** (`knowledge_agent.py`) - Intelligent reasoning engine with MCP tools
- **Voice Agent** (`voice_agent.py`) - Client that sends queries and receives responses

### Core Components
- **`messages.py`** - A2A communication protocols
- **`tools/`** - MCP tools and ASI:One reasoning engine
  - `pacos_tools.py` - Stateless MCP tool functions
  - `asi_one_reasoning.py` - Intelligent reasoning with Claude

## 🚀 Quick Start

1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure API Keys:**
   Create `.env` file with:
   ```
   ANTHROPIC_API_KEY=your_anthropic_key
   GOOGLE_API_KEY=your_google_key
   GOOGLE_CSE_ID=your_cse_id
   ```

3. **Run the System:**
   ```bash
   # Terminal 1 - Start PACoS Brain
   python knowledge_agent.py
   
   # Terminal 2 - Start Voice Agent
   python voice_agent.py
   ```

## 🔧 Features

- **Intelligent Tool Selection** - Claude decides which tools to use
- **Smart Query Analysis** - Extracts intent and optimizes search terms
- **Real-time Web Search** - Google Custom Search integration
- **Natural Responses** - AI-generated conversational responses
- **A2A Communication** - Seamless agent-to-agent messaging

## 📁 Project Structure

```
feedcast/
├── knowledge_agent.py      # PACoS Brain (MCP Server)
├── voice_agent.py          # Voice Agent (A2A Client)
├── messages.py              # A2A Protocol Models
├── tools/                  # MCP Tools & Reasoning
│   ├── pacos_tools.py     # Tool functions
│   └── asi_one_reasoning.py # ASI:One reasoning engine
├── requirements.txt        # Dependencies
├── .env                   # API keys (create this)
└── README.md              # This file
```

## 🎯 How It Works

1. **Voice Agent** sends queries every 10 seconds
2. **PACoS Brain** receives queries and analyzes them with Claude
3. **ASI:One Reasoning** decides if live data is needed
4. **MCP Tools** execute web searches or use memory
5. **Claude** synthesizes natural responses
6. **A2A Response** sent back to Voice Agent

## 🧪 Testing

The system automatically tests with the query: "Hey Chief, what is the current price of gold right now?"

Watch the logs to see:
- Intelligent query analysis
- Tool selection decisions
- Search execution
- Response synthesis