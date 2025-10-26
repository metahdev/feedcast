"""
Pydantic models for the AI podcast generation system.
"""

from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field, validator
from datetime import datetime
from enum import Enum


class ComplexityLevel(str, Enum):
    """User complexity level preferences."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    EXPERT = "expert"


class Tone(str, Enum):
    """Podcast tone preferences."""
    CASUAL = "casual"
    PROFESSIONAL = "professional"
    ACADEMIC = "academic"
    CONVERSATIONAL = "conversational"


class Pace(str, Enum):
    """Podcast pace preferences."""
    SLOW = "slow"
    MODERATE = "moderate"
    FAST = "fast"


class VoicePreference(str, Enum):
    """Voice format preferences."""
    SINGLE = "single"
    DIALOGUE = "dialogue"
    INTERVIEW = "interview"
    NARRATIVE = "narrative"


class SegmentType(str, Enum):
    """Podcast segment types."""
    NEWS_OF_DAY = "news_of_day"
    DEEP_DIVE = "deep_dive"
    QUICK_HITS = "quick_hits"
    INTRO = "intro"
    OUTRO = "outro"


class Format(str, Enum):
    """Podcast format types."""
    MONOLOGUE = "monologue"
    DIALOGUE = "dialogue"
    INTERVIEW = "interview"
    NARRATIVE = "narrative"


class VerificationStatus(str, Enum):
    """Fact-check verification status."""
    VERIFIED = "verified"
    PARTIALLY_VERIFIED = "partially_verified"
    UNVERIFIED = "unverified"
    DISPUTED = "disputed"


class UserPreferences(BaseModel):
    """User preferences for podcast generation."""
    complexity_level: ComplexityLevel = Field(
        default=ComplexityLevel.INTERMEDIATE,
        description="Content complexity level"
    )
    tone: Tone = Field(
        default=Tone.CONVERSATIONAL,
        description="Preferred podcast tone"
    )
    pace: Pace = Field(
        default=Pace.MODERATE,
        description="Preferred speaking pace"
    )
    preferred_length: int = Field(
        default=30,
        ge=5,
        le=120,
        description="Preferred podcast length in minutes"
    )
    segment_preferences: Dict[str, bool] = Field(
        default={
            "news_of_day": True,
            "deep_dive": True,
            "quick_hits": True
        },
        description="Segment type preferences"
    )
    voice_preference: VoicePreference = Field(
        default=VoicePreference.SINGLE,
        description="Preferred voice format"
    )

    @validator('segment_preferences')
    def validate_segment_preferences(cls, v):
        """Validate segment preferences contain expected keys."""
        expected_keys = {"news_of_day", "deep_dive", "quick_hits"}
        if not all(key in expected_keys for key in v.keys()):
            raise ValueError("segment_preferences must contain news_of_day, deep_dive, and quick_hits")
        return v


class PodcastSegmentRequest(BaseModel):
    """Request for generating a specific podcast segment."""
    type: SegmentType = Field(description="Type of segment to generate")
    duration_minutes: int = Field(
        ge=1,
        le=60,
        description="Duration of segment in minutes"
    )
    topics: Optional[List[str]] = Field(
        default=None,
        description="Specific topics to cover in this segment"
    )
    priority: int = Field(
        default=1,
        ge=1,
        le=5,
        description="Priority level (1=highest, 5=lowest)"
    )

    @validator('topics')
    def validate_topics(cls, v):
        """Validate topics list."""
        if v is not None and len(v) == 0:
            raise ValueError("topics list cannot be empty")
        return v


class GenerationRequest(BaseModel):
    """Main request for podcast generation."""
    user_id: str = Field(description="ID of the user requesting generation")
    format: Format = Field(description="Overall podcast format")
    duration_minutes: int = Field(
        ge=5,
        le=120,
        description="Total podcast duration in minutes"
    )
    segments: List[PodcastSegmentRequest] = Field(
        description="List of segments to include in the podcast"
    )
    interactive_elements_count: int = Field(
        default=3,
        ge=0,
        le=10,
        description="Number of interactive elements to include"
    )

    @validator('segments')
    def validate_segments(cls, v):
        """Validate segments list."""
        if len(v) == 0:
            raise ValueError("segments list cannot be empty")
        
        # Check for required segment types
        segment_types = [seg.type for seg in v]
        if SegmentType.INTRO not in segment_types:
            raise ValueError("segments must include an intro segment")
        if SegmentType.OUTRO not in segment_types:
            raise ValueError("segments must include an outro segment")
        
        return v

    @validator('duration_minutes')
    def validate_duration_vs_segments(cls, v, values):
        """Validate total duration matches segment durations."""
        if 'segments' in values:
            total_segment_duration = sum(seg.duration_minutes for seg in values['segments'])
            if abs(total_segment_duration - v) > 5:  # Allow 5 minute tolerance
                raise ValueError("Total segment duration should match podcast duration")
        return v


class Source(BaseModel):
    """Source information for fact-checking and citations."""
    url: str = Field(description="Source URL")
    title: str = Field(description="Source title")
    publication: str = Field(description="Publication name")
    credibility_score: float = Field(
        ge=0.0,
        le=1.0,
        description="Credibility score (0.0 to 1.0)"
    )
    content_summary: str = Field(
        max_length=500,
        description="Brief summary of source content"
    )
    published_date: Optional[datetime] = Field(
        default=None,
        description="Publication date"
    )

    @validator('url')
    def validate_url(cls, v):
        """Basic URL validation."""
        if not v.startswith(('http://', 'https://')):
            raise ValueError("URL must start with http:// or https://")
        return v


class FactCheck(BaseModel):
    """Fact-checking information for podcast content."""
    claim: str = Field(
        max_length=200,
        description="The claim being fact-checked"
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence level in verification (0.0 to 1.0)"
    )
    verification_status: VerificationStatus = Field(
        description="Status of fact verification"
    )
    sources: List[Source] = Field(
        description="Sources used for verification"
    )
    notes: Optional[str] = Field(
        default=None,
        max_length=300,
        description="Additional verification notes"
    )

    @validator('sources')
    def validate_sources(cls, v):
        """Validate sources list."""
        if len(v) == 0:
            raise ValueError("sources list cannot be empty")
        return v


class Participant(BaseModel):
    """Participant information for multi-voice podcasts."""
    name: str = Field(description="Participant name")
    role: str = Field(description="Role in the podcast")
    voice_characteristics: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Voice characteristics for TTS"
    )


class Segment(BaseModel):
    """Podcast segment with timing and content."""
    type: SegmentType = Field(description="Segment type")
    start_time: float = Field(ge=0, description="Start time in seconds")
    duration: float = Field(ge=0, description="Duration in seconds")
    content: str = Field(description="Segment content/script")
    participants: List[str] = Field(
        description="Participant names for this segment"
    )
    transitions: Optional[List[str]] = Field(
        default=None,
        description="Transition phrases"
    )


class Transition(BaseModel):
    """Transition between segments."""
    from_segment: str = Field(description="Source segment")
    to_segment: str = Field(description="Target segment")
    transition_type: Literal["smooth", "abrupt", "musical", "voice_over"] = Field(
        description="Type of transition"
    )
    duration: float = Field(
        ge=0,
        le=10,
        description="Transition duration in seconds"
    )
    content: Optional[str] = Field(
        default=None,
        description="Transition content/script"
    )


class LiveKitScript(BaseModel):
    """Complete script for LiveKit podcast generation."""
    total_duration_estimate: float = Field(
        ge=0,
        description="Total estimated duration in seconds"
    )
    participants: List[Participant] = Field(
        description="List of participants"
    )
    segments: List[Segment] = Field(
        description="List of podcast segments"
    )
    transitions: List[Transition] = Field(
        description="List of segment transitions"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata"
    )
    fact_checks: List[FactCheck] = Field(
        default_factory=list,
        description="Fact-checking information"
    )

    @validator('segments')
    def validate_segments_timing(cls, v):
        """Validate segment timing doesn't overlap."""
        for i, segment in enumerate(v):
            for j, other_segment in enumerate(v):
                if i != j:
                    # Check for overlap
                    if (segment.start_time < other_segment.start_time + other_segment.duration and
                        segment.start_time + segment.duration > other_segment.start_time):
                        raise ValueError(f"Segments {i} and {j} have overlapping timing")
        return v

    @validator('transitions')
    def validate_transitions(cls, v, values):
        """Validate transitions reference existing segments."""
        if 'segments' not in values:
            return v
        
        segment_names = [seg.type.value for seg in values['segments']]
        for transition in v:
            if transition.from_segment not in segment_names:
                raise ValueError(f"Transition references non-existent segment: {transition.from_segment}")
            if transition.to_segment not in segment_names:
                raise ValueError(f"Transition references non-existent segment: {transition.to_segment}")
        return v


# Response models for API endpoints
class GenerationResponse(BaseModel):
    """Response for podcast generation request."""
    request_id: str = Field(description="Unique request identifier")
    status: Literal["pending", "processing", "completed", "failed"] = Field(
        description="Generation status"
    )
    livekit_script: Optional[LiveKitScript] = Field(
        default=None,
        description="Generated LiveKit script"
    )
    estimated_completion_time: Optional[datetime] = Field(
        default=None,
        description="Estimated completion time"
    )
    error_message: Optional[str] = Field(
        default=None,
        description="Error message if generation failed"
    )


class RecommendationResponse(BaseModel):
    """Response for podcast recommendations."""
    recommendations: List[Dict[str, Any]] = Field(
        description="List of podcast recommendations"
    )
    user_profile_summary: Dict[str, Any] = Field(
        description="Summary of user profile used for recommendations"
    )
    generation_timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When recommendations were generated"
    )
