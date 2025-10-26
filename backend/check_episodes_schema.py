"""
Quick script to check what columns actually exist in the episodes table.
"""

import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
supabase = create_client(supabase_url, supabase_key)

print("=" * 80)
print("📊 CHECKING EPISODES TABLE SCHEMA")
print("=" * 80)

# Try to get any episode to see what columns exist
try:
    result = supabase.table("episodes").select("*").limit(1).execute()
    
    if result.data:
        print("\n✅ Found episodes in database")
        print(f"\nColumns in episodes table:")
        print("-" * 40)
        for key in result.data[0].keys():
            print(f"  - {key}")
        print("-" * 40)
    else:
        print("\nℹ️  No episodes found in database")
        print("Let's try to query the schema directly...")
        
        # Try a minimal insert to see what columns are required
        print("\n🔍 Attempting to discover required columns...")
        print("(This will fail, but the error will tell us what columns exist)")
        
        try:
            supabase.table("episodes").insert({"test": "value"}).execute()
        except Exception as e:
            error_msg = str(e)
            print(f"\nError (expected): {error_msg}")
            
            if "not null" in error_msg.lower():
                print("\n📋 Required (NOT NULL) columns found in error message")
            
except Exception as e:
    print(f"\n❌ Error querying episodes: {e}")
    print("\nLet me check what tables exist...")
    
    # List all tables we can access
    tables_to_check = ["episodes", "podcasts", "episode_topics", "sources", "fact_checks"]
    print("\n📋 Checking accessible tables:")
    for table_name in tables_to_check:
        try:
            result = supabase.table(table_name).select("*").limit(0).execute()
            print(f"  ✅ {table_name} - accessible")
        except Exception as table_error:
            print(f"  ❌ {table_name} - {table_error}")

print("\n" + "=" * 80)

