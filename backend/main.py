r"""
Main FastAPI application for the Feedcast podcast generation system.
Integrates all services and provides comprehensive API endpoints.
"""

import os
import logging
from typing import Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import services
from clean_agent.agent_core import CleanAgent
from podcast_generation.clean_agent_integration import init_podcast_routes
from routers.podcast_router import router as podcast_router
from podcast_generation.claude_service import ClaudePodcastService
from podcast_generation.fact_checker import FactChecker
from podcast_generation.generator import PodcastGenerator
from clean_agent.services.supabase_client import SupabaseClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Feedcast Podcast Generation API",
    description="AI-powered podcast generation system with fact-checking and personalization",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global service instances
agent = None
claude_service = None
fact_checker = None
podcast_generator = None
supabase_client = None

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    global agent, claude_service, fact_checker, podcast_generator, supabase_client
    
    logger.info("Starting up Feedcast Podcast Generation API...")
    
    try:
        # Initialize Clean Agent
        logger.info("Initializing Clean Agent...")
        agent = CleanAgent()
        
        # Verify Anthropic API key
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        if not anthropic_key:
            logger.error("ANTHROPIC_API_KEY environment variable not set")
            raise HTTPException(status_code=500, detail="Anthropic API key not configured")
        
        # Initialize Supabase client
        logger.info("Initializing Supabase client...")
        try:
            supabase_client_instance = SupabaseClient()
            if not supabase_client_instance.is_connected():
                logger.warning("Supabase connection failed - running in limited mode")
                supabase_client = None
            else:
                supabase_client = supabase_client_instance.client
        except Exception as e:
            logger.warning(f"Supabase initialization failed: {e} - running in limited mode")
            supabase_client = None
        
        # Initialize Claude service
        logger.info("Initializing Claude service...")
        claude_service = ClaudePodcastService(api_key=anthropic_key)
        
        # Initialize Fact Checker
        logger.info("Initializing Fact Checker...")
        fact_checker = FactChecker(claude_service)
        
        # Initialize Podcast Generator
        logger.info("Initializing Podcast Generator...")
        podcast_generator = PodcastGenerator(supabase_client, claude_service, fact_checker)
        
        logger.info("All services initialized successfully!")
        
    except Exception as e:
        logger.error(f"Failed to initialize services: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Service initialization failed: {str(e)}")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    global claude_service
    logger.info("Shutting down Feedcast Podcast Generation API...")
    
    if claude_service:
        try:
            await claude_service.close()
        except Exception as e:
            logger.warning(f"Error closing Claude service: {e}")

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled errors."""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error": str(exc)}
    )

# Add existing routes
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Feedcast Podcast Generation API",
        "version": "1.0.0",
        "services": {
            "clean_agent": "active",
            "podcast_generation": "active",
            "claude_service": "active",
            "fact_checker": "active"
        }
    }

@app.post("/chat")
async def chat(message: str):
    """Process a chat message."""
    if not agent:
        raise HTTPException(status_code=500, detail="Clean Agent not initialized")
    
    try:
        response = await agent.process_message(message)
        return {"response": response}
    except Exception as e:
        logger.error(f"Chat processing error: {str(e)}")
        return {"error": str(e)}

# Enhanced health check endpoint
@app.get("/health")
async def health_check():
    """Comprehensive health check for all services."""
    health_status = {
        "status": "healthy",
        "timestamp": "2024-01-01T00:00:00Z",  # Will be updated below
        "services": {}
    }
    
    try:
        from datetime import datetime
        health_status["timestamp"] = datetime.utcnow().isoformat()
        
        # Check Clean Agent
        health_status["services"]["clean_agent"] = {
            "status": "healthy" if agent else "unhealthy",
            "message": "Clean Agent initialized" if agent else "Clean Agent not initialized"
        }
        
        # Check Supabase connection
        if supabase_client:
            try:
                # Test database connection
                result = supabase_client.table("users").select("id").limit(1).execute()
                health_status["services"]["supabase"] = {
                    "status": "healthy",
                    "message": "Database connection successful",
                    "tables_accessible": True
                }
            except Exception as e:
                health_status["services"]["supabase"] = {
                    "status": "unhealthy",
                    "message": f"Database connection failed: {str(e)}",
                    "tables_accessible": False
                }
        else:
            health_status["services"]["supabase"] = {
                "status": "unhealthy",
                "message": "Supabase client not initialized"
            }
        
        # Check Anthropic API
        if claude_service:
            try:
                # Test Claude API with a simple request
                test_response = await claude_service.generate_completion(
                    messages=[{"role": "user", "content": "Hello"}],
                    max_tokens=10
                )
                health_status["services"]["anthropic"] = {
                    "status": "healthy",
                    "message": "Anthropic API accessible",
                    "test_response_length": len(test_response)
                }
            except Exception as e:
                health_status["services"]["anthropic"] = {
                    "status": "unhealthy",
                    "message": f"Anthropic API test failed: {str(e)}"
                }
        else:
            health_status["services"]["anthropic"] = {
                "status": "unhealthy",
                "message": "Claude service not initialized"
            }
        
        # Check Fact Checker
        health_status["services"]["fact_checker"] = {
            "status": "healthy" if fact_checker else "unhealthy",
            "message": "Fact Checker initialized" if fact_checker else "Fact Checker not initialized"
        }
        
        # Check Podcast Generator
        health_status["services"]["podcast_generator"] = {
            "status": "healthy" if podcast_generator else "unhealthy",
            "message": "Podcast Generator initialized" if podcast_generator else "Podcast Generator not initialized"
        }
        
        # Check database tables
        if supabase_client:
            try:
                required_tables = ["users", "podcasts", "sources", "fact_checks", "user_interests", "interactive_elements"]
                table_status = {}
                
                for table in required_tables:
                    try:
                        supabase_client.table(table).select("id").limit(1).execute()
                        table_status[table] = "accessible"
                    except Exception as e:
                        table_status[table] = f"error: {str(e)}"
                
                health_status["services"]["database_tables"] = {
                    "status": "healthy" if all(status == "accessible" for status in table_status.values()) else "partial",
                    "tables": table_status
                }
            except Exception as e:
                health_status["services"]["database_tables"] = {
                    "status": "unhealthy",
                    "message": f"Table check failed: {str(e)}"
                }
        
        # Overall status
        all_healthy = all(
            service.get("status") == "healthy" 
            for service in health_status["services"].values()
        )
        health_status["status"] = "healthy" if all_healthy else "degraded"
        
        return health_status
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }

# Initialize podcast routes (legacy integration)
init_podcast_routes(app)

# Include new podcast router with /api prefix
app.include_router(podcast_router, prefix="/api")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
