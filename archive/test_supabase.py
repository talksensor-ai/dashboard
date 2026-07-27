import os
from dotenv import load_dotenv
from supabase import create_client

# Path to .env in root
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(env_path)

url = os.environ.get("SUPABASE_URL") or os.environ.get("NEXT_PUBLIC_SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE") or os.environ.get("SUPABASE_ANON_KEY")

print("URL:", url)
print("Has Key:", bool(key))

if not url or not key:
    print("Missing credentials")
    exit(1)

supabase = create_client(url, key)
try:
    res = supabase.table("shops").select("*").limit(1).execute()
    print("Shops table query success:", res.data)
except Exception as e:
    print("Shops table query failed:", e)

try:
    res = supabase.table("dialogs").select("*").limit(1).execute()
    print("Dialogs table query success:", res.data)
except Exception as e:
    print("Dialogs table query failed:", e)
