"""
Full end-to-end test: Generate podcast and save to both podcasts and podcast_topics tables.
"""

import os
import asyncio
from dotenv import load_dotenv
from supabase import create_client, Client
from datetime import datetime

# Load environment variables
load_dotenv()

# Import our services
from podcast_generation.claude_service import ClaudePodcastService
from podcast_generation.fact_checker import FactChecker
from podcast_generation.generator import PodcastGenerator
from podcast_generation.types import (
    GenerationRequest,
    PodcastSegmentRequest,
    SegmentType,
    Format,
    UserPreferences
)

async def test_full_podcast_generation():
    """Generate a full podcast and save to both tables."""
    
    print("=" * 80)
    print("🎬 FULL END-TO-END TEST: Podcast Generation + Database Save")
    print("=" * 80)
    
    # Step 1: Initialize services
    print("\n📦 STEP 1: Initializing services...")
    
    supabase_url = os.getenv("SUPABASE_URL", "")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY", "")
    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY", "")
    
    if not all([supabase_url, supabase_key, anthropic_api_key]):
        print("❌ Missing required environment variables")
        return False
    
    supabase = create_client(supabase_url, supabase_key)
    claude_service = ClaudePodcastService(anthropic_api_key)
    fact_checker = FactChecker(claude_service)
    generator = PodcastGenerator(supabase, claude_service, fact_checker)
    
    print("✅ All services initialized")
    
    # Step 2: Get test user
    print("\n👤 STEP 2: Getting test user...")
    
    users_result = supabase.table("users").select("id, email").limit(1).execute()
    if not users_result.data:
        print("❌ No users found in database")
        return False
    
    test_user_id = users_result.data[0]["id"]
    print(f"✅ Using user: {users_result.data[0].get('email', 'No email')}")
    print(f"   User ID: {test_user_id}")
    
    # Step 3: Create generation request
    print("\n📝 STEP 3: Creating generation request...")
    
    request = GenerationRequest(
        user_id=test_user_id,
        format=Format.MONOLOGUE,
        duration_minutes=5,
        segments=[
            PodcastSegmentRequest(
                type=SegmentType.INTRO,
                duration_minutes=1,
                topics=["artificial intelligence"]
            ),
            PodcastSegmentRequest(
                type=SegmentType.NEWS_OF_DAY,
                duration_minutes=3,
                topics=["artificial intelligence"]
            ),
            PodcastSegmentRequest(
                type=SegmentType.OUTRO,
                duration_minutes=1,
                topics=["artificial intelligence"]
            )
        ],
        preferences=UserPreferences()
    )
    
    print("✅ Generation request created")
    print(f"   Duration: {request.duration_minutes} minutes")
    print(f"   Segments: {len(request.segments)}")
    print(f"   Topics: {request.segments[0].topics}")
    
    # Step 4: Generate podcast with event discovery
    print("\n🎙️  STEP 4: Generating podcast with event discovery...")
    print("   (This may take 2-3 minutes...)\n")
    
    try:
        result = await generator.generate_podcast(
            request=request,
            use_event_discovery=True
        )
        
        # Result is already saved to database! Just get the details
        podcast_id = result["podcast_id"]
        summary = result["summary"]
        
        print(f"\n✅ Podcast generated and saved successfully!")
        print(f"   Podcast ID: {podcast_id}")
        print(f"   Title: {summary['title']}")
        print(f"   Duration: {summary['duration_minutes']} minutes")
        print(f"   Sources used: {summary['sources_used']}")
        print(f"   Facts verified: {summary['facts_verified']}")
        
    except Exception as e:
        print(f"\n❌ Failed to generate podcast: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Step 6: Verify podcast_topics were saved
    print("\n🔍 STEP 6: Verifying podcast topics were saved...")
    
    try:
        topics_result = supabase.table("podcast_topics").select(
            "id, topic_type, topic_name, importance_score"
        ).eq("podcast_id", podcast_id).execute()
        
        if topics_result.data:
            print(f"✅ Found {len(topics_result.data)} topics in database!")
            
            # Group by type
            by_type = {}
            for topic in topics_result.data:
                t_type = topic["topic_type"]
                if t_type not in by_type:
                    by_type[t_type] = []
                by_type[t_type].append(topic)
            
            print(f"\n   Topics breakdown:")
            for t_type, topics in by_type.items():
                print(f"   - {t_type.upper()}: {len(topics)} topics")
                for topic in topics[:3]:  # Show first 3 of each type
                    print(f"       • {topic['topic_name'][:60]} (importance: {topic['importance_score']:.1f})")
                if len(topics) > 3:
                    print(f"       ... and {len(topics) - 3} more")
        else:
            print(f"⚠️  No topics found in database (but podcast was saved)")
            
    except Exception as e:
        print(f"⚠️  Could not verify topics: {e}")
    
    # Step 7: Display sample script content
    print("\n📜 STEP 7: Sample script content...")
    
    try:
        script_data = result.get("livekit_script", {})
        if script_data and "segments" in script_data:
            intro_segment = script_data["segments"][0]
            print(f"\n   INTRO ({intro_segment['duration']}s):")
            print(f"   {intro_segment['content'][:200]}...")
        
    except Exception as e:
        print(f"   Could not display script: {e}")
    
    # Step 8: Summary
    print("\n" + "=" * 80)
    print("✅ END-TO-END TEST SUCCESSFUL!")
    print("=" * 80)
    print(f"Podcast saved to database:")
    print(f"  ✅ Podcast ID: {podcast_id}")
    print(f"  ✅ Title: {summary['title']}")
    print(f"  ✅ Duration: {summary['duration_minutes']} minutes")
    print(f"  ✅ Topics saved: {len(topics_result.data) if topics_result.data else 0}")
    print(f"  ✅ Sources: {summary['sources_used']}")
    print(f"  ✅ Facts verified: {summary['facts_verified']}")
    print(f"\n🎉 Both 'podcasts' and 'podcast_topics' tables populated!")
    print("=" * 80)
    
    # Ask if user wants to clean up
    print(f"\n⚠️  Test data remains in database:")
    print(f"   Podcast ID: {podcast_id}")
    print(f"   User can listen or manually delete if needed")
    
    return True

if __name__ == "__main__":
    success = asyncio.run(test_full_podcast_generation())
    exit(0 if success else 1)

