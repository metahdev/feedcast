"""
FastAPI routes for podcast generation system.
Provides comprehensive API endpoints for podcast creation, management, and user interaction.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import asyncio

# Import your existing services
from podcast_generation.types import (
    GenerationRequest, UserPreferences, Source, FactCheck, 
    LiveKitScript, PodcastSegmentRequest, SegmentType, Format
)
from podcast_generation.generator import PodcastGenerator
from podcast_generation.claude_service import ClaudePodcastService
from podcast_generation.fact_checker import FactChecker
from clean_agent.services.supabase_client import SupabaseClient

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api", tags=["podcasts"])

# Response models
class PodcastGenerationResponse(BaseModel):
    """Response for podcast generation request."""
    podcast_id: str = Field(description="Unique podcast identifier")
    status: str = Field(description="Generation status")
    estimated_completion_time: Optional[datetime] = Field(default=None, description="Estimated completion time")
    message: str = Field(description="Status message")

class PodcastDetailResponse(BaseModel):
    """Response for podcast details."""
    id: str
    title: str
    description: str
    format: str
    duration_minutes: int
    status: str
    script: Dict[str, Any]
    sources: List[Dict[str, Any]]
    fact_checks: List[Dict[str, Any]]
    interactive_elements: List[Dict[str, Any]]
    user_preferences: Dict[str, Any]
    generation_metadata: Dict[str, Any]
    created_at: datetime
    updated_at: Optional[datetime] = None

class PodcastListResponse(BaseModel):
    """Response for podcast list."""
    podcasts: List[Dict[str, Any]]
    total_count: int
    page: int
    per_page: int
    has_next: bool
    has_prev: bool

class PodcastStatusResponse(BaseModel):
    """Response for podcast status check."""
    podcast_id: str
    status: str
    progress: int = Field(ge=0, le=100, description="Generation progress percentage")
    message: str
    estimated_completion_time: Optional[datetime] = None

class UserFeedbackRequest(BaseModel):
    """Request model for user feedback."""
    rating: int = Field(ge=1, le=5, description="User rating from 1-5")
    feedback_text: Optional[str] = Field(default=None, max_length=1000, description="Optional feedback text")
    completion_rate: float = Field(ge=0.0, le=1.0, description="How much of the podcast was completed")

class UserFeedbackResponse(BaseModel):
    """Response for user feedback submission."""
    success: bool
    message: str
    feedback_id: Optional[str] = None

class UserInterestResponse(BaseModel):
    """Response for user interests."""
    interests: List[Dict[str, Any]]
    total_count: int

class UserInterestRequest(BaseModel):
    """Request model for adding/updating user interest."""
    interest: str = Field(min_length=1, max_length=100, description="Interest name")
    weight: float = Field(ge=0.0, le=1.0, description="Interest weight/priority")

# Dependency injection
async def get_supabase_client():
    """Get Supabase client instance."""
    client = SupabaseClient()
    if not client.is_connected():
        raise HTTPException(status_code=500, detail="Database connection failed")
    return client.client

async def get_claude_service():
    """Get Claude service instance."""
    return ClaudePodcastService()

async def get_fact_checker(claude_service: ClaudePodcastService = Depends(get_claude_service)):
    """Get FactChecker instance."""
    return FactChecker(claude_service)

async def get_podcast_generator(
    supabase_client = Depends(get_supabase_client),
    claude_service: ClaudePodcastService = Depends(get_claude_service),
    fact_checker: FactChecker = Depends(get_fact_checker)
):
    """Get PodcastGenerator instance."""
    return PodcastGenerator(supabase_client, claude_service, fact_checker)

# Background task for podcast generation
async def generate_news_podcast_background(
    generator: PodcastGenerator,
    request: GenerationRequest,
    user_id: str,
    top_interests: List[str]
):
    """Background task for NEWS episode generation with event discovery."""
    try:
        logger.info(f"🎙️  Starting NEWS episode generation for user {user_id}")
        logger.info(f"   Interests: {', '.join(top_interests)}")
        
        # Generate episode with EVENT DISCOVERY enabled
        result = await generator.generate_podcast(
            request=request,
            use_event_discovery=True  # Use news-style event discovery
        )
        
        # Extract results
        generated_episode_id = result["podcast_id"]  # This is actually episode_id now
        summary = result["summary"]
        
        # Episode already saved by generator
        logger.info(f"✅ NEWS episode generated: {summary['title']}")
        logger.info(f"   Episode ID: {generated_episode_id}")
        logger.info(f"   Topics saved: Check episode_topics table for follow-up queries")
        
    except Exception as e:
        logger.error(f"❌ NEWS episode generation failed for user {user_id}: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())


async def generate_podcast_background(
    generator: PodcastGenerator,
    request: GenerationRequest,
    podcast_id: str
):
    """Background task for podcast generation."""
    try:
        logger.info(f"Starting background generation for podcast {podcast_id}")
        
        # Update status to generating
        generator.supabase.table("podcasts").update({
            "status": "generating",
            "updated_at": datetime.now(timezone.utc).isoformat()
        }).eq("id", podcast_id).execute()
        
        # Generate the podcast
        result = await generator.generate_podcast(request)
        
        # Update status to ready (completed)
        generator.supabase.table("podcasts").update({
            "status": "ready",
            "updated_at": datetime.now(timezone.utc).isoformat()
        }).eq("id", podcast_id).execute()
        
        logger.info(f"Background generation completed for podcast {podcast_id}")
        
    except Exception as e:
        logger.error(f"Background generation failed for podcast {podcast_id}: {str(e)}")
        
        # Update status to failed
        try:
            generator.supabase.table("podcasts").update({
                "status": "failed",
                "error_message": str(e),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }).eq("id", podcast_id).execute()
        except Exception as update_error:
            logger.error(f"Failed to update error status: {update_error}")

# Routes
@router.post("/podcasts/generate-news", response_model=PodcastGenerationResponse)
async def generate_personalized_news_podcast(
    user_id: str = Query(..., description="User ID to generate podcast for"),
    duration_minutes: int = Query(5, ge=1, le=30, description="Podcast duration in minutes"),
    background_tasks: BackgroundTasks = None,
    generator: PodcastGenerator = Depends(get_podcast_generator)
):
    """
    Generate a personalized NEWS podcast based on user interests and persona.
    
    This endpoint:
    1. Fetches user interests from user_interests table
    2. Fetches user persona (occupation, preferences) from users table
    3. Generates AI news based on their interests using event discovery
    4. Creates news-style podcast (not article summaries)
    5. Saves to both podcasts and podcast_topics tables
    
    Returns immediately with podcast_id while generation happens in background.
    """
    try:
        logger.info(f"🎙️  Generating personalized news podcast for user {user_id}")
        
        # 1. Validate user exists
        user_result = generator.supabase.table("users").select("*").eq("id", user_id).single().execute()
        if not user_result.data:
            raise HTTPException(status_code=404, detail="User not found")
        
        user_data = user_result.data
        logger.info(f"✅ User found: {user_data.get('email', 'no email')}")
        
        # 2. Fetch user interests
        interests_result = generator.supabase.table("user_interests").select("interest, weight").eq("user_id", user_id).execute()
        
        if not interests_result.data:
            raise HTTPException(
                status_code=400, 
                detail="No interests found for user. Please add interests first via POST /users/{user_id}/interests"
            )
        
        user_interests = interests_result.data
        logger.info(f"✅ Found {len(user_interests)} interests")
        
        # 3. Extract top interests (sorted by weight)
        sorted_interests = sorted(user_interests, key=lambda x: x.get('weight', 0), reverse=True)
        top_interests = [i['interest'] for i in sorted_interests[:5]]  # Top 5 interests
        
        logger.info(f"📊 Top interests: {', '.join(top_interests)}")
        
        # 4. Create GenerationRequest based on user interests
        segments = [
            PodcastSegmentRequest(
                type=SegmentType.INTRO,
                duration_minutes=1,
                topics=top_interests[:1]  # Main interest for intro
            ),
            PodcastSegmentRequest(
                type=SegmentType.NEWS_OF_DAY,
                duration_minutes=duration_minutes - 2,  # Most of the content
                topics=top_interests  # All top interests
            ),
            PodcastSegmentRequest(
                type=SegmentType.OUTRO,
                duration_minutes=1,
                topics=[]
            )
        ]
        
        # Use user preferences if they exist, otherwise defaults
        user_preferences = UserPreferences(
            complexity_level=user_data.get('complexity_level', 'intermediate'),
            tone=user_data.get('tone', 'conversational'),
            pace=user_data.get('pace', 'moderate'),
            voice_preference=user_data.get('voice_preference', 'single'),
            preferred_length=duration_minutes
        )
        
        request = GenerationRequest(
            user_id=user_id,
            format=Format.MONOLOGUE,  # News podcast is monologue
            duration_minutes=duration_minutes,
            segments=segments,
            preferences=user_preferences
        )
        
        # 5. Start background generation with EVENT DISCOVERY
        # Note: No placeholder needed - generator creates the episode with podcast
        background_tasks.add_task(
            generate_news_podcast_background,
            generator,
            request,
            user_id,  # Pass user_id for tracking
            top_interests
        )
        
        # Estimate completion time (3-4 minutes for research + generation)
        estimated_seconds = 180 + (duration_minutes * 30)  # 3 min base + 30s per minute
        estimated_time = datetime.now(timezone.utc).timestamp() + estimated_seconds
        
        return PodcastGenerationResponse(
            podcast_id=f"generating-{user_id}",  # Temporary ID (episode will be created by generator)
            status="generating",
            estimated_completion_time=datetime.fromtimestamp(estimated_time, tz=timezone.utc),
            message=f"Generating personalized news episode covering: {', '.join(top_interests)}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start news podcast generation: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to start podcast generation: {str(e)}")


@router.post("/podcasts/generate", response_model=PodcastGenerationResponse)
async def generate_podcast(
    request: GenerationRequest,
    background_tasks: BackgroundTasks,
    generator: PodcastGenerator = Depends(get_podcast_generator)
):
    """
    Generate a new podcast based on user preferences and topics.
    
    This endpoint starts the podcast generation process asynchronously.
    Use the status endpoint to check generation progress.
    """
    try:
        logger.info(f"Received podcast generation request for user {request.user_id}")
        
        # Validate user exists
        logger.info(f"Validating user {request.user_id}")
        user_check = generator.supabase.table("users").select("id").eq("id", request.user_id).execute()
        logger.info(f"User check result: {user_check.data}")
        if not user_check.data:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Create initial podcast record
        podcast_result = generator.supabase.table("podcasts").insert({
            "user_id": request.user_id,
            "title": "Generating...",
            "description": "Podcast is being generated",
            "total_duration": request.duration_minutes,
            "status": "generating",
            "created_at": datetime.now(timezone.utc).isoformat()
        }).execute()
        
        podcast_id = podcast_result.data[0]["id"]
        
        # Start background generation
        background_tasks.add_task(
            generate_podcast_background,
            generator,
            request,
            podcast_id
        )
        
        # Estimate completion time (rough estimate based on duration)
        estimated_time = datetime.now(timezone.utc).timestamp() + (request.duration_minutes * 2)  # 2 seconds per minute
        
        return PodcastGenerationResponse(
            podcast_id=podcast_id,
            status="generating",
            estimated_completion_time=datetime.fromtimestamp(estimated_time),
            message="Podcast generation started successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start podcast generation: {str(e)}")
        logger.error(f"Exception type: {type(e).__name__}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to start podcast generation: {str(e)}")

@router.get("/podcasts/{podcast_id}", response_model=PodcastDetailResponse)
async def get_podcast(
    podcast_id: str,
    supabase_client = Depends(get_supabase_client)
):
    """
    Get detailed information about a specific podcast.
    
    Returns the complete podcast data including script, sources, and fact checks.
    """
    try:
        # Get podcast details
        podcast_result = supabase_client.table("podcasts").select("*").eq("id", podcast_id).single().execute()
        
        if not podcast_result.data:
            raise HTTPException(status_code=404, detail="Podcast not found")
        
        podcast = podcast_result.data
        
        # Get related data
        sources_result = supabase_client.table("sources").select("*").eq("podcast_id", podcast_id).execute()
        fact_checks_result = supabase_client.table("fact_checks").select("*").eq("podcast_id", podcast_id).execute()
        interactive_result = supabase_client.table("interactive_elements").select("*").eq("podcast_id", podcast_id).execute()
        
        return PodcastDetailResponse(
            id=podcast["id"],
            title=podcast["title"],
            description=podcast["description"],
            format=podcast["format"],
            duration_minutes=podcast["duration_minutes"],
            status=podcast["status"],
            script=podcast.get("script", {}),
            sources=sources_result.data,
            fact_checks=fact_checks_result.data,
            interactive_elements=interactive_result.data,
            user_preferences=podcast.get("user_preferences", {}),
            generation_metadata=podcast.get("generation_metadata", {}),
            created_at=datetime.fromisoformat(podcast["created_at"].replace("Z", "+00:00")),
            updated_at=datetime.fromisoformat(podcast["updated_at"].replace("Z", "+00:00")) if podcast.get("updated_at") else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get podcast {podcast_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve podcast")

@router.get("/podcasts/user/{user_id}", response_model=PodcastListResponse)
async def get_user_podcasts(
    user_id: str,
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Items per page"),
    supabase_client = Depends(get_supabase_client)
):
    """
    Get all podcasts for a specific user with pagination.
    
    Returns a paginated list of podcasts with engagement metrics.
    """
    try:
        # Validate user exists
        user_check = supabase_client.table("users").select("id").eq("id", user_id).execute()
        if not user_check.data:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Calculate offset
        offset = (page - 1) * per_page
        
        # Get total count
        count_result = supabase_client.table("podcasts").select("id", count="exact").eq("user_id", user_id).execute()
        total_count = count_result.count or 0
        
        # Get paginated podcasts
        podcasts_result = supabase_client.table("podcasts").select(
            "id, title, description, format, duration_minutes, status, created_at, user_rating, completion_rate"
        ).eq("user_id", user_id).order("created_at", desc=True).range(offset, offset + per_page - 1).execute()
        
        # Calculate pagination info
        has_next = (offset + per_page) < total_count
        has_prev = page > 1
        
        return PodcastListResponse(
            podcasts=podcasts_result.data,
            total_count=total_count,
            page=page,
            per_page=per_page,
            has_next=has_next,
            has_prev=has_prev
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get podcasts for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve user podcasts")

@router.get("/podcasts/{podcast_id}/status", response_model=PodcastStatusResponse)
async def get_podcast_status(
    podcast_id: str,
    supabase_client = Depends(get_supabase_client)
):
    """
    Check the generation status of a podcast.
    
    Returns current status and progress information.
    """
    try:
        # Get podcast status
        podcast_result = supabase_client.table("podcasts").select(
            "id, status, created_at, updated_at, error_message"
        ).eq("id", podcast_id).single().execute()
        
        if not podcast_result.data:
            raise HTTPException(status_code=404, detail="Podcast not found")
        
        podcast = podcast_result.data
        status = podcast["status"]
        
        # Calculate progress based on status
        progress_map = {
            "pending": 0,
            "generating": 50,
            "completed": 100,
            "failed": 0
        }
        progress = progress_map.get(status, 0)
        
        # Generate status message
        if status == "pending":
            message = "Podcast generation is queued"
        elif status == "generating":
            message = "Podcast is being generated"
        elif status == "completed":
            message = "Podcast generation completed successfully"
        elif status == "failed":
            message = f"Podcast generation failed: {podcast.get('error_message', 'Unknown error')}"
        else:
            message = f"Unknown status: {status}"
        
        # Estimate completion time for generating status
        estimated_completion = None
        if status == "generating":
            created_at = datetime.fromisoformat(podcast["created_at"].replace("Z", "+00:00"))
            estimated_completion = created_at.timestamp() + 300  # 5 minutes estimate
            estimated_completion = datetime.fromtimestamp(estimated_completion)
        
        return PodcastStatusResponse(
            podcast_id=podcast_id,
            status=status,
            progress=progress,
            message=message,
            estimated_completion_time=estimated_completion
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get status for podcast {podcast_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve podcast status")

@router.post("/podcasts/{podcast_id}/feedback", response_model=UserFeedbackResponse)
async def submit_podcast_feedback(
    podcast_id: str,
    feedback: UserFeedbackRequest,
    supabase_client = Depends(get_supabase_client)
):
    """
    Submit user feedback and rating for a podcast.
    
    Updates the podcast with user engagement data.
    """
    try:
        # Verify podcast exists
        podcast_check = supabase_client.table("podcasts").select("id, user_id").eq("id", podcast_id).single().execute()
        if not podcast_check.data:
            raise HTTPException(status_code=404, detail="Podcast not found")
        
        # Update podcast with feedback
        update_data = {
            "user_rating": feedback.rating,
            "completion_rate": feedback.completion_rate,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        if feedback.feedback_text:
            update_data["user_feedback"] = feedback.feedback_text
        
        supabase_client.table("podcasts").update(update_data).eq("id", podcast_id).execute()
        
        # Save detailed feedback to user_engagement table (if it exists)
        try:
            supabase_client.table("user_engagement").insert({
                "user_id": podcast_check.data["user_id"],
                "podcast_id": podcast_id,
                "rating": feedback.rating,
                "feedback_text": feedback.feedback_text,
                "completion_rate": feedback.completion_rate,
                "created_at": datetime.now(timezone.utc).isoformat()
            }).execute()
        except Exception as e:
            logger.warning(f"Failed to save to user_engagement table: {e}")
        
        return UserFeedbackResponse(
            success=True,
            message="Feedback submitted successfully",
            feedback_id=podcast_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to submit feedback for podcast {podcast_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to submit feedback")

@router.get("/users/{user_id}/interests", response_model=UserInterestResponse)
async def get_user_interests(
    user_id: str,
    supabase_client = Depends(get_supabase_client)
):
    """
    Get all interests for a specific user with their weights.
    
    Returns user interests ordered by weight (highest first).
    """
    try:
        # Validate user exists
        user_check = supabase_client.table("users").select("id").eq("id", user_id).execute()
        if not user_check.data:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get user interests
        interests_result = supabase_client.table("user_interests").select(
            "interest, weight, created_at, updated_at"
        ).eq("user_id", user_id).order("weight", desc=True).execute()
        
        return UserInterestResponse(
            interests=interests_result.data,
            total_count=len(interests_result.data)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get interests for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve user interests")

@router.post("/users/{user_id}/interests")
async def add_user_interest(
    user_id: str,
    interest_request: UserInterestRequest,
    supabase_client = Depends(get_supabase_client)
):
    """
    Add or update a user interest.
    
    If the interest already exists, it will be updated with the new weight.
    """
    try:
        # Validate user exists
        user_check = supabase_client.table("users").select("id").eq("id", user_id).execute()
        if not user_check.data:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check if interest already exists
        existing_interest = supabase_client.table("user_interests").select("id").eq("user_id", user_id).eq("interest", interest_request.interest).execute()
        
        if existing_interest.data:
            # Update existing interest
            supabase_client.table("user_interests").update({
                "weight": interest_request.weight,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }).eq("user_id", user_id).eq("interest", interest_request.interest).execute()
            
            message = "Interest updated successfully"
        else:
            # Add new interest
            supabase_client.table("user_interests").insert({
                "user_id": user_id,
                "interest": interest_request.interest,
                "weight": interest_request.weight,
                "created_at": datetime.now(timezone.utc).isoformat()
            }).execute()
            
            message = "Interest added successfully"
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": message,
                "interest": interest_request.interest,
                "weight": interest_request.weight
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add/update interest for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update user interest")

# Health check endpoint
@router.get("/podcasts/health")
async def health_check():
    """Health check endpoint for the podcast service."""
    return {"status": "healthy", "service": "podcast_generation", "timestamp": datetime.now(timezone.utc).isoformat()}
