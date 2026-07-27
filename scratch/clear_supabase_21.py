import os
from dotenv import load_dotenv
from supabase import create_client

# Load env variables from root directory
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(env_path)

url = os.environ.get("SUPABASE_URL") or os.environ.get("NEXT_PUBLIC_SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE") or os.environ.get("SUPABASE_ANON_KEY")

if not url or not key:
    print("Error: Missing Supabase credentials in .env")
    exit(1)

supabase = create_client(url, key)

date_str = "2026-05-21"
start_timestamp = f"{date_str}T00:00:00.000Z"
end_timestamp = f"{date_str}T23:59:59.999Z"

print(f"Clearing dialogues for date {date_str} (created_at between {start_timestamp} and {end_timestamp}) for shop_id = 8...")

try:
    # First, query to see how many dialogues exist
    query_res = supabase.table("dialogs").select("id, created_at, dialog_index").eq("shop_id", 8).gte("created_at", start_timestamp).lte("created_at", end_timestamp).execute()
    existing_count = len(query_res.data) if query_res.data else 0
    print(f"Found {existing_count} dialogues for this date range.")
    
    if existing_count > 0:
        # Delete them
        delete_res = supabase.table("dialogs").delete().eq("shop_id", 8).gte("created_at", start_timestamp).lte("created_at", end_timestamp).execute()
        print(f"Successfully deleted {len(delete_res.data)} dialogues from Supabase.")
    else:
        print("No dialogues to delete.")
        
except Exception as e:
    print("Error interacting with Supabase:", e)
    exit(1)
