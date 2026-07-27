import json

with open('e:/talk/scratch/dialogs_dump.json', encoding='utf-8') as f:
    dialogs = json.load(f)

# Group by original_audio_file or dialogue_index/time
# Let's filter to dialogues from 2026-05-21
target_dialogs = [d for d in dialogs if '2026-05-21' in d.get('created_at', '')]

# Group by original_audio_file
grouped = {}
for d in target_dialogs:
    audio = d.get('original_audio_file')
    if not audio:
        continue
    grouped.setdefault(audio, []).append(d)

with open('e:/talk/scratch/comparison_output.txt', 'w', encoding='utf-8') as out:
    out.write(f"Total grouped dialogues: {len(grouped)}\n\n")
    for audio, group in sorted(grouped.items()):
        out.write(f"Audio File: {audio}\n")
        out.write("="*100 + "\n")
        for d in group:
            out.write(f"  ID: {d['id']} | Dialog Index: {d.get('dialog_index')} | Score: {d.get('score')} | Created At: {d.get('created_at')}\n")
            out.write(f"  Audit: {json.dumps(d.get('audit_details'), ensure_ascii=False)}\n")
            out.write(f"  Text Analysis:\n{d.get('text_analysis')}\n")
            out.write(f"  Clean Text Snippet: {d.get('clean_text', '')[:200]}...\n")
            out.write("-"*80 + "\n")
        out.write("\n" + "="*100 + "\n\n")

print("Done! comparison_output.txt generated.")
