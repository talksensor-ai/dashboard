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

# Get some dialogs
res = supabase.table("dialogs").select("id, dialog_index, original_audio_file, audio_url, transcript, score, created_at").order("id", desc=True).limit(30).execute()

for d in res.data:
    print(f"ID: {d['id']}, Index: {d['dialog_index']}, Created: {d['created_at']}")
    print(f"  Original Audio File: {d['original_audio_file']}")
    print(f"  Audio URL: {d['audio_url']}")
    
    transcript = d.get("transcript", [])
    if transcript:
        first_line = transcript[0]
        last_line = transcript[-1]
        print(f"  Transcript len: {len(transcript)} lines")
        print(f"    First: [{first_line.get('start')} - {first_line.get('end')}] ({first_line.get('speaker')}): {first_line.get('text')}")
        print(f"    Last: [{last_line.get('start')} - {last_line.get('end')}] ({last_line.get('speaker')}): {last_line.get('text')}")
    else:
        print("  Transcript is empty")
    print("-" * 50)
