import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv('E:/talk/.env')

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE")

if not url or not key:
    print("Credentials missing!")
    exit(1)

supabase = create_client(url, key)
res = supabase.table("dialogs").select("id, dialog_index, original_audio_file, audio_url, created_at").order("created_at", desc=False).execute()
print(f"Total dialogs: {len(res.data)}")
for d in res.data:
    print(f"ID: {d['id']} | Index: {d['dialog_index']} | File: {d['original_audio_file']} | Date: {d['created_at']}")
    print(f"  URL: {d['audio_url']}")
