import json

with open('e:/talk/scratch/dialogs_dump.json', encoding='utf-8') as f:
    dialogs = json.load(f)

print(f"Total dumped dialogues: {len(dialogs)}")
for d in dialogs:
    print(f"ID: {d['id']} | Index: {d['dialog_index']} | Date: {d['created_at']}")
    text_analysis = d.get('text_analysis', '')
    audit_details = d.get('audit_details') or {}
    print(f"  Analysis snippet: {str(text_analysis)[:120]}")
    print(f"  Audit keys: {list(audit_details.keys())}")
    print("-" * 50)
