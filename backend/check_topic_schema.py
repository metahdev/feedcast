"""Check episode_topics table schema"""
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY"))

print("=" * 80)
print("📊 CHECKING EPISODE_TOPICS TABLE SCHEMA")
print("=" * 80)

try:
    result = supabase.table("episode_topics").select("*").limit(1).execute()
    
    if result.data:
        print("\n✅ Found episode_topics in database")
        print(f"\nColumns in episode_topics table:")
        print("-" * 40)
        for key in result.data[0].keys():
            print(f"  - {key}")
        print("-" * 40)
    else:
        print("\nℹ️  No episode_topics found - table is empty")
        print("Attempting minimal insert to discover schema...")
        try:
            supabase.table("episode_topics").insert({"test": "value"}).execute()
        except Exception as e:
            print(f"\nSchema discovery error: {e}")
            
except Exception as e:
    print(f"\n❌ Error: {e}")

print("=" * 80)

