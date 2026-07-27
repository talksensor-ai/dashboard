import os
from supabase import create_client

url = os.environ.get('NEXT_PUBLIC_SUPABASE_URL') or 'https://itllqtmuvktatmpalzxo.supabase.co'
key = os.environ.get('SUPABASE_SERVICE_ROLE') or os.environ.get('NEXT_PUBLIC_SUPABASE_ANON_KEY') or 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Iml0bGxxdG11dmt0YXRtcGFsenhvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzkyNTg2NjUsImV4cCI6MjA5NDgzNDY2NX0.APM2hf8Tj4fYMfZvjXMgOKmVBSu0LhfESBz-zx0QaKQ'
sb = create_client(url, key)

res = sb.table('dialogs').select('id, transcript, created_at').order('created_at', desc=False).execute()
dialogs_may21 = [r for r in res.data if '2026-05-21' in r['created_at']]

print(f"Total dialogs for May 21: {len(dialogs_may21)}")
for i, d in enumerate(dialogs_may21):
    transcript = d['transcript']
    print(f"\n=== Dialog Index {i+1} (ID {d['id']}) ===")
    payments = 0
    for t in transcript:
        if 'оплат' in t['text'].lower() or 'прикладывай' in t['text'].lower() or 'здравствуйте' in t['text'].lower() or 'добрый' in t['text'].lower():
            print(f"{t['speaker']}: {t['text']}")
        if 'прикладывай' in t['text'].lower() or 'оплат' in t['text'].lower():
            payments += 1
    if payments >= 2:
        print(f"!!! MULTIPLE PAYMENTS FOUND in ID {d['id']}")
