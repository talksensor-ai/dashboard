import os
from supabase import create_client

url = os.environ.get('NEXT_PUBLIC_SUPABASE_URL') or 'https://itllqtmuvktatmpalzxo.supabase.co'
key = os.environ.get('SUPABASE_SERVICE_ROLE') or os.environ.get('NEXT_PUBLIC_SUPABASE_ANON_KEY') or 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Iml0bGxxdG11dmt0YXRtcGFsenhvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzkyNTg2NjUsImV4cCI6MjA5NDgzNDY2NX0.APM2hf8Tj4fYMfZvjXMgOKmVBSu0LhfESBz-zx0QaKQ'
sb = create_client(url, key)

res = sb.table('dialogs').select('id, transcript').eq('id', 51).execute()
if res.data:
    transcript = res.data[0]['transcript']
    for t in transcript:
        if 'придиктовать' in t['text'].lower() or 'александр' in t['text'].lower() or '978' in t['text']:
            print(f"BEFORE: {t['speaker']}: {t['text']}")
            
        if 'придиктовать' in t['text'].lower():
            t['speaker'] = 'БАРИСТА'
            t['text'] = t['text'].replace('придиктовать', 'продиктовать').replace('Придиктовать', 'Продиктовать')
        if 'кофельсинчик' in t['text'].lower():
            t['text'] = t['text'].replace('кофельсинчик', 'кофе апельсинчик').replace('Кофельсинчик', 'Кофе апельсинчик')

    sb.table('dialogs').update({'transcript': transcript}).eq('id', 51).execute()
    print('Dialog 51 patched!')
