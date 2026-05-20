import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv('e:/talk/.env')
sb = create_client(os.environ['SUPABASE_URL'], os.environ['SUPABASE_SERVICE_ROLE'])

# Get 13:00 dialogs (Dialog 10, 11, 12 correspond to the 13:00 file probably)
res = sb.table('dialogs').select('id, dialog_index, created_at, clean_text, audit_details, text_analysis').eq('original_audio_file', '2026-04-24_13-00-24-04-2026.ogg').order('dialog_index').execute()

for d in res.data:
    print(f"=== DIALOG {d['dialog_index']} (ID: {d['id']}) ===")
    print(f"Time: {d['created_at']}")
    print(f"Type: {d['audit_details'].get('dialogue_type')}")
    print(f"Text:\n{d['clean_text']}\n")
    print(f"Reasoning/Analysis:\n{d['text_analysis']}\n")
