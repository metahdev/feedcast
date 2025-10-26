"""
Simple example: Generate a podcast for a user with interests.
Run this after your FastAPI server is running.
"""

import requests
import time
import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

# Configuration
API_URL = "http://localhost:8000"
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

def generate_podcast_for_user(user_id: str, duration_minutes: int = 5):
    """
    Generate a personalized news podcast for a user.
    
    Args:
        user_id: User's UUID from users table
        duration_minutes: Podcast duration (5-30 minutes)
    """
    
    print("=" * 80)
    print(f"🎙️  GENERATING PODCAST FOR USER: {user_id}")
    print("=" * 80)
    
    # Step 1: Verify user and interests
    print("\n📊 Step 1: Checking user and interests...")
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # Check user exists
    user = supabase.table("users").select("email").eq("id", user_id).single().execute()
    if not user.data:
        print(f"❌ User {user_id} not found!")
        return
    
    print(f"✅ User found: {user.data.get('email', 'no email')}")
    
    # Check interests
    interests = supabase.table("user_interests").select("interest, weight").eq("user_id", user_id).execute()
    
    if not interests.data:
        print("⚠️  No interests found - adding sample interests...")
        supabase.table("user_interests").insert([
            {"user_id": user_id, "interest": "artificial intelligence", "weight": 10},
            {"user_id": user_id, "interest": "technology", "weight": 8},
            {"user_id": user_id, "interest": "science", "weight": 6}
        ]).execute()
        interests = supabase.table("user_interests").select("interest, weight").eq("user_id", user_id).execute()
    
    sorted_interests = sorted(interests.data, key=lambda x: x.get('weight', 0), reverse=True)
    top_interests = [i['interest'] for i in sorted_interests[:5]]
    
    print(f"✅ Found {len(interests.data)} interests:")
    for interest in sorted_interests[:5]:
        print(f"   - {interest['interest']} (weight: {interest['weight']})")
    
    # Step 2: Call API to generate podcast
    print(f"\n🚀 Step 2: Calling API to generate {duration_minutes}-minute podcast...")
    print("   (This starts background generation)")
    
    try:
        response = requests.post(
            f"{API_URL}/api/podcasts/generate-news",
            params={
                "user_id": user_id,
                "duration_minutes": duration_minutes
            },
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ Generation started!")
            print(f"   Status: {result['status']}")
            print(f"   Message: {result['message']}")
            print(f"   Estimated wait: ~3 minutes")
            
            # Step 3: Wait for completion
            print(f"\n⏳ Step 3: Waiting for completion...")
            print("   (Generation takes 2-4 minutes for event discovery)")
            
            wait_time = 180  # 3 minutes
            for i in range(wait_time, 0, -30):
                print(f"   {i}s remaining...", end='\r')
                time.sleep(30)
            
            print("\n✅ Wait complete! Checking results...")
            
            # Step 4: Check results
            print(f"\n📺 Step 4: Checking for generated episode...")
            
            # Get latest episode for user via podcast relationship
            episodes = supabase.table("episodes").select(
                "id, title, duration, created_at, podcast:podcasts!inner(user_id)"
            ).order("created_at", desc=True).limit(5).execute()
            
            user_episodes = [e for e in episodes.data if e.get('podcast', {}).get('user_id') == user_id]
            
            if user_episodes:
                episode = user_episodes[0]
                print(f"\n🎉 Episode created successfully!")
                print(f"   ID: {episode['id']}")
                print(f"   Title: {episode['title']}")
                print(f"   Duration: {episode['duration']}s")
                print(f"   Created: {episode['created_at']}")
                
                # Get topics
                topics = supabase.table("episode_topics").select("*").eq("episode_id", episode['id']).execute()
                
                if topics.data:
                    print(f"\n📝 Topics saved ({len(topics.data)} total):")
                    for topic in sorted(topics.data, key=lambda t: t['importance_score'], reverse=True)[:5]:
                        print(f"   - {topic['topic_name']} ({topic['topic_type']}, score: {topic['importance_score']:.1f})")
                
                # Get sources
                sources = supabase.table("sources").select("title, publication").eq("episode_id", episode['id']).execute()
                
                if sources.data:
                    print(f"\n📰 Sources used ({len(sources.data)} total):")
                    for source in sources.data[:3]:
                        print(f"   - {source['title']} ({source['publication']})")
                
                print("\n" + "=" * 80)
                print("✅ SUCCESS! Podcast generated and saved to database.")
                print("=" * 80)
                
                return episode['id']
            
            else:
                print(f"\n⚠️  Episode not found yet.")
                print("   Generation may still be in progress or failed.")
                print("   Check your FastAPI logs for details.")
                return None
            
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"   {response.text}")
            return None
            
    except requests.exceptions.ConnectionError:
        print("\n❌ Could not connect to API!")
        print("   Make sure your FastAPI server is running:")
        print("   cd /Users/Tim/Desktop/Berkeley/hackathon/feedcast/backend")
        print("   uvicorn main:app --reload")
        return None
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    # Example: Get first user and generate podcast
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    print("Finding a user to test with...")
    users = supabase.table("users").select("id, email").limit(5).execute()
    
    if not users.data:
        print("❌ No users found in database!")
        exit(1)
    
    # Use first user (or change index)
    test_user = users.data[0]
    user_id = test_user["id"]
    
    print(f"\n📋 Available users:")
    for i, user in enumerate(users.data):
        print(f"   {i}: {user.get('email', 'no email')} ({user['id']})")
    
    print(f"\n🎯 Using user: {test_user.get('email', 'no email')}")
    print(f"   ID: {user_id}")
    
    # Generate 5-minute podcast
    episode_id = generate_podcast_for_user(user_id, duration_minutes=5)
    
    if episode_id:
        print(f"\n🎊 All done! Episode ID: {episode_id}")
        print(f"\n💡 To generate for a different user:")
        print(f"   python generate_podcast_example.py")
        print(f"\n💡 To use in your code:")
        print(f"   import requests")
        print(f"   requests.post('http://localhost:8000/api/podcasts/generate-news?user_id={user_id}&duration_minutes=5')")
    else:
        print("\n❌ Generation failed. Check logs for details.")

