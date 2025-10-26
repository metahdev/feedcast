# 🎙️ Feedcast Project Structure Outline

## 📁 Project Overview
Feedcast is a multi-platform podcast application with AI-powered content generation, consisting of:
- **iOS App** (Swift/SwiftUI)
- **Backend Services** (Python/FastAPI)
- **AI Integration** (Claude + Search)
- **Database** (Supabase)

---

## 🏗️ Directory Structure

### 📱 **iOS Application** (`/feedcast/`)
```
feedcast/
├── Assets.xcassets/           # App icons and color assets
├── ContentView.swift          # Main app view
├── feedcastApp.swift         # App entry point
├── Models/                   # Data models
│   ├── ChatMessage.swift     # Chat message model
│   ├── Interest.swift        # User interest model
│   ├── Podcast.swift         # Podcast model
│   └── User.swift           # User model
├── Services/                 # API services
│   ├── ChatService.swift     # Chat functionality
│   ├── PodcastService.swift  # Podcast operations
│   └── UserService.swift     # User management
├── ViewModels/              # MVVM view models
│   ├── InterestsViewModel.swift
│   ├── LibraryViewModel.swift
│   └── PlayerViewModel.swift
└── Views/                   # SwiftUI views
    ├── InterestsView.swift
    ├── LibraryView.swift
    └── PlayerView.swift
```

### 🖥️ **Backend Services** (`/backend/`)

#### **Clean Agent** (`/backend/clean_agent/`)
```
clean_agent/
├── __init__.py
├── agent_core.py            # Core agent logic
├── app.py                   # FastAPI application
├── README_CLEAN.md          # Documentation
├── services/                # Service layer
│   ├── __init__.py
│   ├── claude_service.py    # Claude AI integration
│   ├── memory_service.py    # Memory management
│   ├── search_adapter.py    # Search functionality
│   └── supabase_client.py   # Database client
└── tests/                   # Unit tests
    ├── __init__.py
    └── test_clean_agent.py
```

#### **Podcast Generation** (`/backend/podcast_generation/`) - **NEW**
```
podcast_generation/
├── __init__.py
├── clean_agent_integration.py  # FastAPI routes integration
├── podcast_generator.py        # Main generation logic
├── recommendation_engine.py    # AI recommendation system
└── services/                   # Specialized services
    ├── claude_podcast_service.py  # Claude for podcast content
    └── podcast_db_service.py      # Database operations
```

### 🧠 **AI & Tools** (`/tools/`, `/services/`)

#### **Core AI Tools** (`/tools/`)
```
tools/
├── __init__.py
├── asi_one_reasoning.py     # Advanced reasoning engine
├── context_enricher.py      # Context enhancement
├── intent_classifier.py     # Intent classification
├── live_search_tool.py      # Web search capabilities
├── pacos_tools.py          # Core utility functions
└── reasoning_engine.py     # Reasoning logic
```

#### **AI Services** (`/services/`)
```
services/
├── claude_reflection_service.py  # Claude reflection
├── enhanced_memory_service.py    # Memory management
└── summarization_service.py      # Content summarization
```

### 📚 **Archive** (`/archive/`)
```
archive/                     # Legacy/experimental code
├── ARCHITECTURE.md          # System architecture docs
├── knowledge_agent.py       # Original knowledge agent
├── voice_agent.py          # Voice interaction agent
├── messages.py             # Communication protocol
├── enhanced_reasoning_engine.py
├── final_fixed_engine.py
├── fixed_reasoning_engine.py
├── interactive_test.py
├── quick_chat.py
├── start_agents.py
├── show_full_response.py
├── debug_live_search.py
├── chat_interface.py
├── test_*.py               # Various test files
├── *.md                    # Documentation files
├── *.db                    # Database files
├── requirements.txt        # Python dependencies
└── supabase_setup.sql      # Database schema
```

### 🐍 **Python Environment** (`/venv/`)
```
venv/                       # Virtual environment
├── bin/                    # Executables
├── include/                # Header files
├── lib/                    # Python packages
├── share/                  # Shared resources
└── pyvenv.cfg             # Environment config
```

---

## 🔄 **System Architecture Flow**

### **1. iOS App Layer**
- **Views**: User interface components
- **ViewModels**: Business logic and state management
- **Services**: API communication with backend
- **Models**: Data structures

### **2. Backend API Layer**
- **FastAPI App**: REST API endpoints
- **Clean Agent**: Core AI processing
- **Podcast Generation**: AI-powered content creation

### **3. AI Processing Layer**
- **Claude Integration**: Content generation and analysis
- **Search Tools**: Web search and information gathering
- **Reasoning Engine**: Decision making and logic

### **4. Data Layer**
- **Supabase**: User data, interests, podcast history
- **Memory Services**: User preferences and context
- **Database Services**: CRUD operations

---

## 🚀 **Key Features by Component**

### **iOS App**
- User interest management
- Podcast library and playback
- Chat interface for AI interaction
- Personalized recommendations

### **Backend Services**
- AI-powered chat responses
- Podcast content generation
- User profile management
- Recommendation engine

### **AI Integration**
- Live web search
- Content analysis and summarization
- Personalized recommendations
- Context-aware responses

---

## 📊 **Data Flow**

```
User Input (iOS) 
    ↓
API Endpoints (FastAPI)
    ↓
Clean Agent (Processing)
    ↓
AI Services (Claude + Search)
    ↓
Database (Supabase)
    ↓
Response (iOS)
```

---

## 🛠️ **Development Setup**

### **Prerequisites**
- Python 3.13+ with virtual environment
- Xcode for iOS development
- Supabase account and credentials
- Anthropic API key for Claude

### **Key Dependencies**
- **Backend**: FastAPI, Anthropic, Supabase, uvicorn
- **AI**: Claude API, web search tools
- **iOS**: SwiftUI, Combine framework

---

## 📈 **Project Status**

### ✅ **Completed**
- iOS app structure and basic UI
- Backend API framework
- AI reasoning engine
- Database integration
- **NEW**: Podcast generation system

### 🚧 **In Progress**
- iOS app functionality
- Backend service integration
- AI content generation

### 📋 **Planned**
- Audio generation and processing
- Advanced personalization
- Social features
- Analytics and insights

---

## 🔧 **Recent Additions**

The **Podcast Generation System** adds:
- AI-powered topic recommendations
- Content structure generation
- Show notes creation
- User preference integration
- FastAPI endpoints for podcast operations

This creates a complete pipeline from user interests to generated podcast content, leveraging Claude's capabilities for intelligent content creation.
