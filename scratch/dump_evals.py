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
res = supabase.table("dialogs").select("id, dialog_index, score, text_analysis, audit_details, created_at").order("created_at", desc=False).execute()
print(f"Total dialogs: {len(res.data)}")
for d in res.data:
    print(f"ID: {d['id']} | Index: {d['dialog_index']} | Score: {d['score']} | Date: {d['created_at']}")
    print(f"  Analysis snippet: {str(d['text_analysis'])[:200]}")
    print(f"  Audit details: {str(d['audit_details'])[:200]}")
    print("-" * 50)
