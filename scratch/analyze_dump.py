import json
import os

dump_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'scratch', 'dialogs_dump.json')
with open(dump_path, 'r', encoding='utf-8') as f:
    dialogs = json.load(f)

print(f"Total dialogs: {len(dialogs)}")
for idx, d in enumerate(dialogs):
    # Get transcript times
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
    
    print(f"Row {idx+1}: DB_ID={d['id']}, DB_Index={d['dialog_index']}, Created={d['created_at']}")
    print(f"  Times: [{min_start} - {max_end}] seconds")
    print(f"  Original Audio: {original_audio}")
    print(f"  Audio URL: {audio_url}")
    print(f"  Clean Text Snippet: {d.get('clean_text', '')[:100]}...")
    print("-" * 50)
