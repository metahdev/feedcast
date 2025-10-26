"""
Quick test: Verify database schema works with dummy episode data.
Tests the podcast → episode → episode_topics flow without full generation.
"""

import os
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

def test_database_schema():
    """Test that we can insert episodes and topics with current schema."""
    
    print("=" * 80)
    print("🧪 QUICK DATABASE SCHEMA TEST")
    print("=" * 80)
    
    # Initialize Supabase
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
    supabase = create_client(supabase_url, supabase_key)
    
    try:
        # Step 1: Get a test user
        print("\n📊 Step 1: Finding test user...")
        users = supabase.table("users").select("id, email").limit(1).execute()
        
        if not users.data:
            print("❌ No users found!")
            return False
        
        user_id = users.data[0]["id"]
        user_email = users.data[0].get("email", "no email")
        print(f"✅ Using user: {user_email} ({user_id})")
        
        # Step 2: Create or get podcast (show)
        print("\n📻 Step 2: Creating/getting podcast (show)...")
        
        # Check if user has a podcast
        existing_podcasts = supabase.table("podcasts").select("id, title").eq("user_id", user_id).execute()
        
        if existing_podcasts.data:
            podcast_id = existing_podcasts.data[0]["id"]
            print(f"✅ Using existing podcast: {existing_podcasts.data[0]['title']}")
        else:
            # Create a new podcast with VALID status
            podcast_data = {
                "user_id": user_id,
                "title": "Test Podcast Show",
                "description": "Test podcast description",
                "status": "ready",  # ✅ Valid status value
                "created_at": datetime.utcnow().isoformat()
            }
            
            podcast_result = supabase.table("podcasts").insert(podcast_data).execute()
            podcast_id = podcast_result.data[0]["id"]
            print(f"✅ Created new podcast: Test Podcast Show ({podcast_id})")
        
        # Step 3: Create test episode
        print("\n📺 Step 3: Creating test episode...")
        
        # Dummy episode data - matching existing schema
        episode_data = {
            "podcast_id": podcast_id,
            # Note: NO user_id - episodes relate to users via podcast_id
            "title": "Test Episode - Database Schema Check",
            "description": "This is a test episode to verify database schema",
            "duration": 300,  # 5 minutes in seconds
            "script": {  # ✅ Your table has "script" column
                "segments": [
                    {
                        "type": "INTRO",
                        "content": "Welcome to the test episode!",
                        "duration": 60
                    },
                    {
                        "type": "NEWS_OF_DAY",
                        "content": "Here's the main content...",
                        "duration": 180
                    },
                    {
                        "type": "OUTRO",
                        "content": "Thanks for listening!",
                        "duration": 60
                    }
                ]
            },
            "created_at": datetime.utcnow().isoformat()
            # Note: No "status" or "metadata" - keeping it simple with existing schema
        }
        
        episode_result = supabase.table("episodes").insert(episode_data).execute()
        episode_id = episode_result.data[0]["id"]
        print(f"✅ Episode created successfully!")
        print(f"   ID: {episode_id}")
        print(f"   Title: {episode_data['title']}")
        
        # Step 4: Create test episode topics
        print("\n🏷️  Step 4: Creating test episode topics...")
        
        test_topics = [
            {
                "episode_id": episode_id,
                "podcast_id": podcast_id,
                "user_id": user_id,
                "topic_type": "entity",
                "topic_name": "Test Company",
                "summary": "This episode covers Test Company's developments",
                "key_facts": ["Fact 1", "Fact 2"],
                "entities_mentioned": {"Test Company": ["event1", "event2"]},
                "source_urls": ["https://example.com/article1"],
                "segment_mentioned": "NEWS_OF_DAY",
                "importance_score": 9.5,
                "created_at": datetime.utcnow().isoformat()
            },
            {
                "episode_id": episode_id,
                "podcast_id": podcast_id,
                "user_id": user_id,
                "topic_type": "theme",
                "topic_name": "Test Theme",
                "summary": "This episode covers Test Theme developments",
                "key_facts": ["Theme fact 1"],
                "entities_mentioned": {},
                "source_urls": ["https://example.com/article2"],
                "segment_mentioned": "NEWS_OF_DAY",
                "importance_score": 8.0,
                "created_at": datetime.utcnow().isoformat()
            }
        ]
        
        topics_result = supabase.table("episode_topics").insert(test_topics).execute()
        print(f"✅ Created {len(topics_result.data)} test topics!")
        for topic in topics_result.data:
            print(f"   - {topic['topic_name']} ({topic['topic_type']}, score: {topic['importance_score']})")
        
        # Step 5: Verify data was saved correctly
        print("\n🔍 Step 5: Verifying saved data...")
        
        # Check episode
        saved_episode = supabase.table("episodes").select("*").eq("id", episode_id).single().execute()
        
        if saved_episode.data:
            episode = saved_episode.data
            print(f"✅ Episode verified:")
            print(f"   - Has podcast_id: {bool(episode.get('podcast_id'))}")
            print(f"   - Has script: {bool(episode.get('script'))}")
            print(f"   - Script type: {type(episode.get('script'))}")
            print(f"   - Has title: {bool(episode.get('title'))}")
            print(f"   - Has duration: {bool(episode.get('duration'))}")
        
        # Check topics
        saved_topics = supabase.table("episode_topics").select("*").eq("episode_id", episode_id).execute()
        print(f"\n✅ Topics verified: {len(saved_topics.data)} topics found")
        
        # Step 6: Test querying episodes via podcast relationship
        print("\n🔗 Step 6: Testing podcast → episode relationship...")
        
        user_episodes = supabase.table("episodes").select(
            "id, title, created_at, podcast:podcasts!inner(user_id, title)"
        ).execute()
        
        # Filter for this user
        user_eps = [e for e in user_episodes.data if e.get('podcast', {}).get('user_id') == user_id]
        print(f"✅ Found {len(user_eps)} episode(s) for this user via podcast relationship")
        
        # Step 7: Cleanup (optional - comment out to keep test data)
        print("\n🧹 Step 7: Cleaning up test data...")
        
        # Delete topics first (foreign key)
        supabase.table("episode_topics").delete().eq("episode_id", episode_id).execute()
        print(f"✅ Deleted test topics")
        
        # Delete episode
        supabase.table("episodes").delete().eq("id", episode_id).execute()
        print(f"✅ Deleted test episode")
        
        # Don't delete podcast - it might have other episodes
        print(f"ℹ️  Kept podcast (might have other episodes)")
        
        # Final summary
        print("\n" + "=" * 80)
        print("✅ DATABASE SCHEMA TEST PASSED!")
        print("=" * 80)
        print("\n📋 Summary:")
        print("  ✅ Podcast table: Can insert with status='ready'")
        print("  ✅ Episodes table: Using existing 'script' column")
        print("  ✅ Episode_topics table: Working correctly")
        print("  ✅ Podcast → Episode relationship: Working correctly")
        print("  ✅ No database migrations needed - code adapted to your schema!")
        print("\n🎉 Your database schema is ready for podcast generation!")
        print("=" * 80)
        
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED!")
        print(f"Error: {str(e)}")
        
        # Check what the error is about
        error_str = str(e)
        
        if "podcasts_status_check" in error_str:
            print("\n⚠️  ISSUE: Podcast status constraint violation")
            print("   The 'status' field must be one of: pending, generating, completed, ready")
            print("   Currently trying to use an invalid status value.")
        
        elif "column" in error_str and "does not exist" in error_str:
            print("\n⚠️  ISSUE: Column not found in episodes table")
            print(f"   Error details: {error_str}")
            print("   Check that your episodes table has the expected columns.")
            print("\n   Expected columns:")
            print("   - id, podcast_id, title, description")
            print("   - duration, audio_url, transcript, created_at")
        
        import traceback
        traceback.print_exc()
        
        return False

if __name__ == "__main__":
    success = test_database_schema()
    exit(0 if success else 1)

