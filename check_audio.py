import os
from dotenv import load_dotenv
from supabase import create_client
load_dotenv("e:/talk/.env")
sb = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_ROLE"])
res = sb.table("dialogs").select("id, audio_url, transcript").eq("shop_id", 8).order("created_at").limit(3).execute()
for r in res.data:
    audio = r.get("audio_url") or "NULL"
    transcript = str(r.get("transcript", ""))[:100] if r.get("transcript") else "NULL"
    print(f"id={r['id']}")
    print(f"  audio_url={audio}")
    print(f"  transcript={transcript}")
    print()
