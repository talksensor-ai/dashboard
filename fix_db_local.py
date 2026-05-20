import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv('e:/talk/.env')
sb = create_client(os.environ['SUPABASE_URL'], os.environ['SUPABASE_SERVICE_ROLE'])
res = sb.table('dialogs').select('id, original_audio_file, created_at').execute()

updates = 0
for r in res.data:
    fname = r.get('original_audio_file', '')
    hour = "12"
    if fname and "_" in fname:
        part = fname.split("_")[-1]
        if "-" in part:
            possible_hour = part.split("-")[0]
            if possible_hour.isdigit():
                hour = possible_hour
    elif fname and "-" in fname:
        possible_hour = fname.split("-")[0]
        if possible_hour.isdigit():
            hour = possible_hour
            
    old_time = r.get('created_at', '')
    if old_time and 'T12:' in old_time and hour != "12":
        new_time = old_time.replace('T12:', f'T{hour}:')
        print(f"Updating {r['id']} from {old_time} to {new_time}")
        try:
            sb.table('dialogs').update({'created_at': new_time}).eq('id', r['id']).execute()
            updates += 1
        except Exception as e:
            print(f"Error updating {r['id']}: {e}")

print(f"Updated {updates} records with correct hour.")
