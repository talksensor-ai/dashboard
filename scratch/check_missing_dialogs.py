import subprocess
import json
import os
from dotenv import load_dotenv
from supabase import create_client

# Load DB credentials
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(env_path)

sb_url = os.environ.get("SUPABASE_URL")
sb_key = os.environ.get("SUPABASE_SERVICE_ROLE") or os.environ.get("SUPABASE_ANON_KEY")

if not sb_url or not sb_key:
    print("Missing Supabase credentials!")
    exit(1)

sb = create_client(sb_url, sb_key)

# 1. Fetch indices from Supabase for May 21
res = sb.table("dialogs").select("dialog_index", "created_at").eq("shop_id", 8).execute()
db_indices = sorted([d['dialog_index'] for d in res.data if d.get('created_at') and '2026-05-21' in d['created_at']])
print("DB indices count:", len(db_indices))
print("DB indices:", db_indices)

# 2. Fetch results from Mac Mini
cmd = ["ssh", "ai@100.123.93.21", "cat /Users/ai/talk/pipeline/results_2026-05-21.json"]
mac_json = subprocess.check_output(cmd).decode("utf-8", errors="ignore")
mac_data = json.loads(mac_json)
mac_results = mac_data.get("results", [])
mac_indices = sorted([r['idx'] for r in mac_results])
print("Mac indices count:", len(mac_indices))
print("Mac indices:", mac_indices)

# 3. Find missing indices
missing = [idx for idx in mac_indices if idx not in db_indices]
print("Missing indices in DB:", missing)

# 4. Check if they were marked as duplicate in the log or if they just failed due to timeout
# Let's inspect the files/logs for those missing indexes
