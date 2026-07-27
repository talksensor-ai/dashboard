import json

with open('e:/talk/scratch/dialogs_dump.json', encoding='utf-8') as f:
    dialogs = json.load(f)

may21 = [d for d in dialogs if '2026-05-21' in d.get('created_at', '')]
print(f"Total May 21 dialogues: {len(may21)}")

for d in sorted(may21, key=lambda x: (x.get('dialog_index', 0), x.get('created_at', ''))):
    print(f"ID: {d['id']} | Index: {d.get('dialog_index')} | Created At: {d.get('created_at')} | Score: {d.get('score')}")
    audit = d.get('audit_details') or {}
    print(f"  Audit: upsell={audit.get('upsell_score')}, cross={audit.get('cross_sales_score')}, loyalty={audit.get('loyalty_score')}, live={audit.get('live_service_score')}")
    print(f"  Snippet: {d.get('clean_text', '')[:100]}...")
    print("-" * 50)
