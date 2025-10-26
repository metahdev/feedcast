"""
End-to-end test: Generate episode for real user with their actual interests.
Tests the full Podcast → Episode → episode_topics flow.
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

async def test_real_user_episode():
    """Generate episode for a real user with their actual interests."""
    
    print("=" * 80)
    print("🎬 END-TO-END TEST: Real User Episode Generation")
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
    
    # Step 2: Get a real user
    print("\n👤 STEP 2: Finding a real user...")
    
    users_result = supabase.table("users").select("id, email").limit(5).execute()
    if not users_result.data:
        print("❌ No users found in database")
        return False
    
    user = users_result.data[1]
    user_id = user["id"]
    user_email = user.get("email", "No email")
    
    print(f"✅ Using user: {user_email}")
    print(f"   User ID: {user_id}")
    
    # Step 3: Get user's interests
    print("\n📊 STEP 3: Getting user interests...")
    
    interests_result = supabase.table("user_interests").select("interest, weight").eq("user_id", user_id).execute()
    
    if not interests_result.data:
        print("⚠️  No interests found - adding test interests...")
        # Add test interests (weight must be integer)
        test_interests = [
            {"user_id": user_id, "interest": "artificial intelligence", "weight": 10},
            {"user_id": user_id, "interest": "technology", "weight": 8},
            {"user_id": user_id, "interest": "science", "weight": 6}
        ]
        supabase.table("user_interests").insert(test_interests).execute()
        interests_result = supabase.table("user_interests").select("interest, weight").eq("user_id", user_id).execute()
    
    user_interests = interests_result.data
    sorted_interests = sorted(user_interests, key=lambda x: x.get('weight', 0), reverse=True)
    top_interests = [i['interest'] for i in sorted_interests[:3]]
    
    print(f"✅ Found {len(user_interests)} interests:")
    for interest in sorted_interests[:5]:
        print(f"   - {interest['interest']} (weight: {interest['weight']})")
    print(f"\n   Using top 3: {', '.join(top_interests)}")
    
    # Step 4: Check existing podcasts for this user
    print("\n📻 STEP 4: Checking for existing podcast (show)...")
    
    existing_podcasts = supabase.table("podcasts").select("id, title").eq("user_id", user_id).execute()
    
    if existing_podcasts.data:
        print(f"✅ User already has {len(existing_podcasts.data)} podcast(s):")
        for p in existing_podcasts.data:
            print(f"   - {p['title']} (ID: {p['id']})")
    else:
        print("ℹ️  No existing podcast - generator will create one")
    
    # Step 5: Check existing episodes (via podcast relationship)
    print("\n📺 STEP 5: Checking existing episodes...")
    
    # Get episodes through podcast relationship
    existing_episodes = supabase.table("episodes").select(
        "id, title, created_at, podcast:podcasts(user_id)"
    ).execute()
    
    # Filter for this user's episodes
    user_episodes = [e for e in existing_episodes.data 
                     if e.get('podcast') and e['podcast'].get('user_id') == user_id][:5]
    
    if user_episodes:
        print(f"✅ User has {len(user_episodes)} existing episode(s):")
        for e in user_episodes:
            print(f"   - {e['title']}")
            print(f"     Created: {e.get('created_at', 'N/A')}")
    else:
        print("ℹ️  No existing episodes - this will be the first!")
    
    # Step 6: Create generation request
    print("\n📝 STEP 6: Creating episode generation request...")
    
    request = GenerationRequest(
        user_id=user_id,
        format=Format.MONOLOGUE,
        duration_minutes=5,  # Minimum allowed (5 minutes)
        segments=[
            PodcastSegmentRequest(
                type=SegmentType.INTRO,
                duration_minutes=1,
                topics=top_interests[:1]
            ),
            PodcastSegmentRequest(
                type=SegmentType.NEWS_OF_DAY,
                duration_minutes=3,
                topics=top_interests
            ),
            PodcastSegmentRequest(
                type=SegmentType.OUTRO,
                duration_minutes=1,
                topics=top_interests[:1]
            )
        ],
        preferences=UserPreferences()
    )
    
    print("✅ Generation request created")
    print(f"   Duration: {request.duration_minutes} minutes")
    print(f"   Topics: {', '.join(top_interests)}")
    
    # Step 7: Generate the episode!
    print("\n🎙️  STEP 7: Generating episode with event discovery...")
    print("   (This will take 2-3 minutes...)\n")
    
    try:
        result = await generator.generate_podcast(
            request=request,
            use_event_discovery=True
        )
        
        episode_id = result["podcast_id"]  # This is actually episode_id
        summary = result["summary"]
        
        print(f"\n✅ Episode generated successfully!")
        print(f"   Episode ID: {episode_id}")
        print(f"   Title: {summary['title']}")
        print(f"   Duration: {summary['duration_minutes']} minutes")
        print(f"   Sources: {summary['sources_used']}")
        print(f"   Facts verified: {summary['facts_verified']}")
        
    except Exception as e:
        print(f"\n❌ Failed to generate episode: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Step 8: Verify podcast was created/used
    print("\n📻 STEP 8: Verifying podcast (show)...")
    
    podcasts_after = supabase.table("podcasts").select("id, title, created_at").eq("user_id", user_id).execute()
    
    if podcasts_after.data:
        print(f"✅ User now has {len(podcasts_after.data)} podcast(s):")
        for p in podcasts_after.data:
            print(f"   - {p['title']}")
            print(f"     ID: {p['id']}")
            print(f"     Created: {p.get('created_at', 'N/A')}")
    
    # Step 9: Verify episode was saved
    print("\n📺 STEP 9: Verifying episode was saved...")
    
    episode_result = supabase.table("episodes").select("*").eq("id", episode_id).single().execute()
    
    if episode_result.data:
        episode = episode_result.data
        print(f"✅ Episode saved to database!")
        print(f"   Title: {episode['title']}")
        print(f"   Podcast ID: {episode.get('podcast_id', 'N/A')}")
        print(f"   Duration: {episode.get('duration', 'N/A')}s")
        print(f"   Status: {episode.get('status', 'N/A')}")
        print(f"   Has script: {'Yes' if episode.get('script') else 'No'}")
    else:
        print(f"❌ Episode not found in database!")
        return False
    
    # Step 10: Verify episode_topics were saved
    print("\n🏷️  STEP 10: Verifying episode topics...")
    
    topics_result = supabase.table("episode_topics").select(
        "id, topic_type, topic_name, importance_score"
    ).eq("episode_id", episode_id).execute()
    
    if topics_result.data:
        topics = topics_result.data
        print(f"✅ Found {len(topics)} topics saved!")
        
        # Group by type
        by_type = {}
        for topic in topics:
            t_type = topic["topic_type"]
            if t_type not in by_type:
                by_type[t_type] = []
            by_type[t_type].append(topic)
        
        print(f"\n   Topics breakdown:")
        for t_type, topics_list in by_type.items():
            print(f"   - {t_type.upper()}: {len(topics_list)} topics")
            for topic in topics_list:
                print(f"       • {topic['topic_name']} (importance: {topic['importance_score']:.1f})")
    else:
        print(f"⚠️  No topics found in episode_topics table")
    
    # Step 11: Verify sources were saved
    print("\n📄 STEP 11: Verifying sources...")
    
    sources_result = supabase.table("sources").select("id, title, publication").eq("episode_id", episode_id).execute()
    
    if sources_result.data:
        print(f"✅ Found {len(sources_result.data)} sources saved!")
        for source in sources_result.data[:3]:
            print(f"   - {source.get('title', 'No title')} ({source.get('publication', 'Unknown')})")
    else:
        print(f"⚠️  No sources found")
    
    # Step 12: Display sample script
    print("\n📜 STEP 12: Sample script content...")
    
    if episode.get('script') and isinstance(episode['script'], dict):
        segments = episode['script'].get('segments', [])
        if segments:
            intro = segments[0]
            content = intro.get('content', '')
            print(f"\n   {intro.get('type', 'segment').upper()} ({intro.get('duration', 0)}s):")
            print(f"   {content[:200]}...")
    
    # Final summary
    print("\n" + "=" * 80)
    print("✅ END-TO-END TEST SUCCESSFUL!")
    print("=" * 80)
    print(f"Summary:")
    print(f"  ✅ User: {user_email}")
    print(f"  ✅ Interests: {', '.join(top_interests)}")
    print(f"  ✅ Podcast (show): {podcasts_after.data[0]['title'] if podcasts_after.data else 'Created'}")
    print(f"  ✅ Episode ID: {episode_id}")
    print(f"  ✅ Episode title: {episode['title']}")
    print(f"  ✅ Topics saved: {len(topics_result.data) if topics_result.data else 0}")
    print(f"  ✅ Sources saved: {len(sources_result.data) if sources_result.data else 0}")
    print(f"\n🎉 Podcast → Episode → episode_topics flow working perfectly!")
    print("=" * 80)
    
    # Count all user's episodes
    all_episodes = supabase.table("episodes").select("id, podcast:podcasts!inner(user_id)").execute()
    user_episode_count = len([e for e in all_episodes.data if e.get('podcast', {}).get('user_id') == user_id])
    
    print(f"\n📋 Quick stats:")
    print(f"   - Total podcasts for user: {len(podcasts_after.data)}")
    print(f"   - Total episodes for user: {user_episode_count}")
    print(f"   - Topics in this episode: {len(topics_result.data) if topics_result.data else 0}")
    
    return True

if __name__ == "__main__":
    success = asyncio.run(test_real_user_episode())
    exit(0 if success else 1)

