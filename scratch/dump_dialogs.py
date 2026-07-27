import os
import json
from dotenv import load_dotenv
from supabase import create_client

env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(env_path)

sb_url = os.environ.get("SUPABASE_URL")
sb_key = os.environ.get("SUPABASE_SERVICE_ROLE") or os.environ.get("SUPABASE_ANON_KEY")

if not sb_url or not sb_key:
    print("Missing Supabase credentials!")
    exit(1)

supabase = create_client(sb_url, sb_key)

# Fetch all dialogs sorted by created_at or id
res = supabase.table("dialogs").select("*").order("id", desc=False).execute()

# Write to a JSON file
out_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'scratch', 'dialogs_dump.json')
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(res.data, f, ensure_ascii=False, indent=2)

print(f"Dumped {len(res.data)} dialogs to {out_path}")
