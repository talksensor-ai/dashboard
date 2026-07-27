import json
import os

dump_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'scratch', 'dialogs_dump.json')
with open(dump_path, 'r', encoding='utf-8') as f:
    dialogs = json.load(f)

# Filter by selectedDate '2026-05-21' and sort chronologically by created_at
date_dialogs = [d for d in dialogs if d.get("created_at", "").startswith("2026-05-21")]
date_dialogs.sort(key=lambda d: d.get("created_at", ""))

print(f"Total dialogs for 2026-05-21: {len(date_dialogs)}")
for idx, d in enumerate(date_dialogs):
    transcript = d.get("transcript", [])
    if transcript:
        starts = [t.get("start") for t in transcript if t.get("start") is not None]
        ends = [t.get("end") for t in transcript if t.get("end") is not None]
        min_start = min(starts) if starts else "N/A"
        max_end = max(ends) if ends else "N/A"
    else:
        min_start, max_end = "EMPTY", "EMPTY"
        
    audio_url = d.get("audio_url") or "NONE"
    original_audio = d.get("original_audio_file") or "NONE"
    
    print(f"Index {idx+1} (UI Dialog #{idx+1}):")
    print(f"  DB ID: {d['id']}")
    print(f"  Created At: {d['created_at']}")
    print(f"  Transcript Range: [{min_start} - {max_end}] seconds")
    print(f"  Audio File: {original_audio}")
    print(f"  Audio URL: {audio_url}")
    print(f"  Clean Text: {d.get('clean_text', '')[:120]}...")
    print("-" * 60)
