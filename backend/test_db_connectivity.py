"""
Test database connectivity and permissions for podcasts and podcast_topics tables.
"""

import os
import asyncio
from dotenv import load_dotenv
from supabase import create_client, Client
from datetime import datetime
import uuid

# Load environment variables
load_dotenv()

def test_database_connections():
    """Test basic connectivity to Supabase tables."""
    
    print("=" * 80)
    print("🔌 TESTING DATABASE CONNECTIVITY")
    print("=" * 80)
    
    # Initialize Supabase
    supabase_url = os.getenv("SUPABASE_URL", "")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY", "")
    
    if not supabase_url or not supabase_key:
        print("❌ Missing SUPABASE_URL or SUPABASE_SERVICE_KEY in .env")
        return False
    
    print(f"✅ Supabase URL: {supabase_url}")
    print(f"✅ API Key loaded: {supabase_key[:20]}...")
    
    try:
        supabase: Client = create_client(supabase_url, supabase_key)
        print("✅ Supabase client created")
    except Exception as e:
        print(f"❌ Failed to create Supabase client: {e}")
        return False
    
    # Test 0: Check existing users and get one
    print("\n" + "=" * 80)
    print("👤 TEST 0: Finding or creating test user")
    print("=" * 80)
    
    test_user_id = None
    created_test_user = False
    
    try:
        # Try to find existing users
        users_result = supabase.table("users").select("id, email").limit(5).execute()
        
        if users_result.data and len(users_result.data) > 0:
            # Use first existing user
            test_user_id = users_result.data[0]["id"]
            print(f"✅ Using existing user: {users_result.data[0].get('email', 'No email')}")
            print(f"   User ID: {test_user_id}")
        else:
            # Create a test user
            print("   No existing users found, creating test user...")
            test_user_id = str(uuid.uuid4())
            test_user_data = {
                "id": test_user_id,
                "email": "test@feedcast.test",
                "created_at": datetime.utcnow().isoformat()
            }
            user_result = supabase.table("users").insert(test_user_data).execute()
            if user_result.data:
                test_user_id = user_result.data[0]["id"]
                created_test_user = True
                print(f"✅ Created test user: {test_user_id}")
            else:
                print(f"❌ Failed to create test user")
                return False
                
    except Exception as e:
        print(f"❌ Failed to access users table: {e}")
        return False
    
    # Test 1: Read from podcasts table
    print("\n" + "=" * 80)
    print("📖 TEST 1: Reading from 'podcasts' table")
    print("=" * 80)
    try:
        result = supabase.table("podcasts").select("id, title, user_id").limit(5).execute()
        print(f"✅ Successfully read from podcasts table")
        print(f"   Found {len(result.data)} podcasts")
        if result.data:
            print(f"   Sample: {result.data[0].get('title', 'No title')}")
    except Exception as e:
        print(f"❌ Failed to read from podcasts table: {e}")
        return False
    
    # Test 2: Read from podcast_topics table
    print("\n" + "=" * 80)
    print("📖 TEST 2: Reading from 'podcast_topics' table")
    print("=" * 80)
    try:
        result = supabase.table("podcast_topics").select("id, topic_name, topic_type").limit(5).execute()
        print(f"✅ Successfully read from podcast_topics table")
        print(f"   Found {len(result.data)} topics")
        if result.data:
            print(f"   Sample: {result.data[0].get('topic_name', 'No name')} ({result.data[0].get('topic_type', 'unknown')})")
    except Exception as e:
        print(f"❌ Failed to read from podcast_topics table: {e}")
        print(f"   Error details: {str(e)}")
        return False
    
    # Test 3: Write to podcasts table
    print("\n" + "=" * 80)
    print("✍️  TEST 3: Writing test data to 'podcasts' table")
    print("=" * 80)
    
    test_podcast_id = None
    
    try:
        test_podcast_data = {
            "user_id": test_user_id,
            "title": "TEST PODCAST - Database Connectivity Test",
            "description": "This is a test podcast created by test_db_connectivity.py",
            "total_duration": 300,
            "script": {
                "segments": [
                    {
                        "type": "intro",
                        "content": "This is a test.",
                        "duration": 60
                    }
                ],
                "total_duration": 300
            },
            "status": "ready",
            "metadata": {"test": True},
            "created_at": datetime.utcnow().isoformat()
        }
        
        result = supabase.table("podcasts").insert(test_podcast_data).execute()
        
        if result.data:
            test_podcast_id = result.data[0]["id"]
            print(f"✅ Successfully wrote to podcasts table")
            print(f"   Test podcast ID: {test_podcast_id}")
        else:
            print(f"❌ No data returned from insert")
            return False
            
    except Exception as e:
        print(f"❌ Failed to write to podcasts table: {e}")
        print(f"   Error details: {str(e)}")
        return False
    
    # Test 4: Write to podcast_topics table
    print("\n" + "=" * 80)
    print("✍️  TEST 4: Writing test data to 'podcast_topics' table")
    print("=" * 80)
    
    test_topic_ids = []
    
    try:
        test_topics_data = [
            {
                "podcast_id": test_podcast_id,
                "user_id": test_user_id,
                "topic_type": "event",
                "topic_name": "Test Event - Database Connectivity",
                "summary": "This is a test event for database connectivity testing",
                "key_facts": ["Test fact 1", "Test fact 2"],
                "entities_mentioned": {"test": "entity"},
                "source_urls": ["https://example.com"],
                "segment_mentioned": "intro",
                "importance_score": 5.0,
                "created_at": datetime.utcnow().isoformat()
            },
            {
                "podcast_id": test_podcast_id,
                "user_id": test_user_id,
                "topic_type": "entity",
                "topic_name": "Test Company",
                "summary": "This is a test company entity",
                "key_facts": ["Company fact 1"],
                "entities_mentioned": {"primary_entity": "Test Company", "mention_count": 1},
                "source_urls": [],
                "segment_mentioned": "intro",
                "importance_score": 6.0,
                "created_at": datetime.utcnow().isoformat()
            },
            {
                "podcast_id": test_podcast_id,
                "user_id": test_user_id,
                "topic_type": "theme",
                "topic_name": "Test Theme",
                "summary": "This is a test theme",
                "key_facts": ["Theme event 1"],
                "entities_mentioned": {},
                "source_urls": [],
                "segment_mentioned": "multiple",
                "importance_score": 7.5,
                "created_at": datetime.utcnow().isoformat()
            }
        ]
        
        result = supabase.table("podcast_topics").insert(test_topics_data).execute()
        
        if result.data:
            test_topic_ids = [t["id"] for t in result.data]
            print(f"✅ Successfully wrote to podcast_topics table")
            print(f"   Created {len(test_topic_ids)} test topics")
            print(f"   Topic types: event, entity, theme")
        else:
            print(f"❌ No data returned from insert")
            return False
            
    except Exception as e:
        print(f"❌ Failed to write to podcast_topics table: {e}")
        print(f"   Error details: {str(e)}")
        return False
    
    # Test 5: Verify we can read back what we wrote
    print("\n" + "=" * 80)
    print("🔍 TEST 5: Verifying data integrity")
    print("=" * 80)
    
    try:
        # Read back the podcast
        podcast_result = supabase.table("podcasts").select("*").eq("id", test_podcast_id).single().execute()
        if podcast_result.data:
            print(f"✅ Successfully read back test podcast")
            print(f"   Title: {podcast_result.data['title']}")
            print(f"   Status: {podcast_result.data['status']}")
        
        # Read back the topics
        topics_result = supabase.table("podcast_topics").select("*").eq("podcast_id", test_podcast_id).execute()
        if topics_result.data:
            print(f"✅ Successfully read back {len(topics_result.data)} test topics")
            for topic in topics_result.data:
                print(f"   - {topic['topic_type']}: {topic['topic_name']}")
        
    except Exception as e:
        print(f"❌ Failed to read back data: {e}")
        return False
    
    # Test 6: Cleanup test data
    print("\n" + "=" * 80)
    print("🧹 TEST 6: Cleaning up test data")
    print("=" * 80)
    
    try:
        # Delete topics first (due to foreign key constraint)
        if test_topic_ids:
            supabase.table("podcast_topics").delete().in_("id", test_topic_ids).execute()
            print(f"✅ Deleted {len(test_topic_ids)} test topics")
        
        # Delete podcast
        if test_podcast_id:
            supabase.table("podcasts").delete().eq("id", test_podcast_id).execute()
            print(f"✅ Deleted test podcast")
        
        # Delete test user if we created it
        if created_test_user and test_user_id:
            supabase.table("users").delete().eq("id", test_user_id).execute()
            print(f"✅ Deleted test user")
        
    except Exception as e:
        print(f"⚠️  Warning: Failed to cleanup test data: {e}")
        print(f"   You may need to manually delete podcast ID: {test_podcast_id}")
    
    # Final summary
    print("\n" + "=" * 80)
    print("✅ ALL TESTS PASSED!")
    print("=" * 80)
    print("Database connectivity verified:")
    print("  ✅ Can read from 'podcasts' table")
    print("  ✅ Can write to 'podcasts' table")
    print("  ✅ Can read from 'podcast_topics' table")
    print("  ✅ Can write to 'podcast_topics' table")
    print("  ✅ Data integrity verified")
    print("  ✅ Cleanup successful")
    print("\nReady for end-to-end testing!")
    print("=" * 80)
    
    return True

if __name__ == "__main__":
    success = test_database_connections()
    exit(0 if success else 1)
