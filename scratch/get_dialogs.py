import os
import json
from supabase import create_client

url = os.environ.get('NEXT_PUBLIC_SUPABASE_URL') or 'https://itllqtmuvktatmpalzxo.supabase.co'
key = os.environ.get('SUPABASE_SERVICE_ROLE') or os.environ.get('NEXT_PUBLIC_SUPABASE_ANON_KEY') or 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Iml0bGxxdG11dmt0YXRtcGFsenhvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzkyNTg2NjUsImV4cCI6MjA5NDgzNDY2NX0.APM2hf8Tj4fYMfZvjXMgOKmVBSu0LhfESBz-zx0QaKQ'
sb = create_client(url, key)

res = sb.table('dialogs').select('id, created_at, audio_url, transcript, clean_text').execute()

dialogs = [r for r in res.data if '2026-05-21' in r['created_at']]
print(f'Found {len(dialogs)} dialogs for May 21st.')
for d in dialogs:
    start_time = d['transcript'][0].get('start') if d.get('transcript') else "None"
    end_time = d['transcript'][-1].get('end') if d.get('transcript') else "None"
    text = d.get('clean_text', '')[:100].replace('\n', ' ')
    print(f"ID: {d['id']}, Audio: {d['audio_url']}, Start: {start_time}, End: {end_time}, Text: {text}")
