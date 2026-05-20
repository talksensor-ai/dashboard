import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv("e:/talk/.env")
sb = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_ROLE"])

res = sb.table("dialogs").select("id, original_audio_file, created_at").eq("original_audio_file", "2026-04-24_13-00-24-04-2026.ogg").execute()

for d in res.data:
    print(f"ID: {d['id']} | Date: {d['created_at']}")
