import os
from supabase import create_client

url = os.environ.get('NEXT_PUBLIC_SUPABASE_URL') or 'https://itllqtmuvktatmpalzxo.supabase.co'
key = os.environ.get('SUPABASE_SERVICE_ROLE') or os.environ.get('NEXT_PUBLIC_SUPABASE_ANON_KEY') or 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Iml0bGxxdG11dmt0YXRtcGFsenhvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzkyNTg2NjUsImV4cCI6MjA5NDgzNDY2NX0.APM2hf8Tj4fYMfZvjXMgOKmVBSu0LhfESBz-zx0QaKQ'
sb = create_client(url, key)

res = sb.table('dialogs').select('id, created_at').execute()
dialogs_may21 = [r['id'] for r in res.data if '2026-05-21' in r['created_at']]

print(f"Deleting {len(dialogs_may21)} dialogs for May 21st...")
if dialogs_may21:
    res = sb.table('dialogs').delete().in_('id', dialogs_may21).execute()
    print("Deleted successfully!")
else:
    print("No dialogs to delete.")
