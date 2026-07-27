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

# Get dialogs for May 21, 2026
res = supabase.table("dialogs").select("id, dialog_index, original_audio_file, audio_url, score, audit_details, created_at").eq("shop_id", 8).order("dialog_index", desc=False).execute()

dialogs_21 = []
for d in res.data:
    created_at = d.get("created_at") or ""
    if "2026-05-21" in created_at:
        dialogs_21.append(d)

print(f"Total dialogs in DB for 2026-05-21: {len(dialogs_21)}")
conflicts = [d for d in dialogs_21 if (d.get("audit_details") or {}).get("is_conflict")]
print(f"Total conflicts: {len(conflicts)}")

for c in conflicts:
    print(f"Conflict Dialog Index: {c['dialog_index']}, ID: {c['id']}")
    print(f"  Audio: {c['original_audio_file']}")
    print(f"  URL: {c['audio_url']}")
    details = c.get("audit_details") or {}
    print(f"  Emotion stats: {details.get('emotion_stats')}")
    print(f"  Recommendation: {details.get('recommendation')}")
    print("-" * 50)
