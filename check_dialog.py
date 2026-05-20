"""Check the dialogue around minute 27 from today's data."""
import os, json
from dotenv import load_dotenv
from supabase import create_client
load_dotenv("e:/talk/.env")

sb = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_ROLE"])
res = sb.table("dialogs").select("id, dialog_index, transcript, audit_details, created_at").eq("shop_id", 8).gte("created_at", "2026-04-24T00:00:00Z").order("created_at").execute()

for r in res.data:
    print(f"\n{'='*60}")
    print(f"Диалог #{r['dialog_index']} (id={r['id']})")
    print(f"created_at: {r['created_at']}")
    if r.get('transcript'):
        for line in r['transcript']:
            mins = int(line.get('start', 0)) // 60
            secs = int(line.get('start', 0)) % 60
            print(f"  [{mins}:{secs:02d}] {line.get('speaker', '?')}: {line.get('text', '')}")
    print()
    if r.get('audit_details'):
        ad = r['audit_details']
        print(f"  dialogue_type: {ad.get('dialogue_type')}")
        print(f"  greeting: {ad.get('greeting_score')}/5")
        print(f"  comment: {ad.get('greeting_comment', 'N/A')}")
