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

# Fetch all dialogs sorted by ID (earliest to latest)
res = supabase.table("dialogs").select("*").order("id", desc=False).execute()
dialogs = res.data

print(f"Total dialogs in database: {len(dialogs)}")

# Group dialogs by date and their transcript start timestamp
seen = {}
to_delete = []

for d in dialogs:
    created_at = d.get("created_at") or ""
    date_str = created_at[:10]  # YYYY-MM-DD
    
    transcript = d.get("transcript", [])
    if not transcript:
        continue
        
    start_ts = min([t.get("start") for t in transcript if t.get("start") is not None], default=None)
    if start_ts is None:
        continue
        
    key = (date_str, start_ts)
    
    if key in seen:
        prev_d = seen[key]
        # Decide which one to keep
        # Rule: Keep the one with a non-empty audio_url, or the one with a higher ID
        prev_has_audio = bool(prev_d.get("audio_url"))
        curr_has_audio = bool(d.get("audio_url"))
        
        if curr_has_audio and not prev_has_audio:
            # Keep current, delete previous
            to_delete.append(prev_d["id"])
            seen[key] = d
            print(f"Duplicate found for {key}: replacing ID {prev_d['id']} (no audio) with ID {d['id']} (has audio)")
        elif prev_has_audio and not curr_has_audio:
            # Keep previous, delete current
            to_delete.append(d["id"])
            print(f"Duplicate found for {key}: keeping ID {prev_d['id']} (has audio), deleting ID {d['id']} (no audio)")
        else:
            # Both have or don't have audio, keep the newer one (higher ID)
            to_delete.append(prev_d["id"])
            seen[key] = d
            print(f"Duplicate found for {key}: keeping newer ID {d['id']}, deleting older ID {prev_d['id']}")
    else:
        seen[key] = d

print(f"IDs marked for deletion: {to_delete}")

if to_delete:
    print(f"Deleting {len(to_delete)} duplicate dialog entries...")
    # Supabase allows delete with in operator
    for id_val in to_delete:
        supabase.table("dialogs").delete().eq("id", id_val).execute()
    print("Deduplication complete!")
else:
    print("No duplicates found to delete.")
