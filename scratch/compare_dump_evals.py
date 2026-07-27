import json

with open('e:/talk/scratch/dialogs_dump.json', encoding='utf-8') as f:
    dialogs = json.load(f)

# Group dialogues by timestamp (created_at)
by_time = {}
for d in dialogs:
    created_at = d['created_at']
    if '2026-05-21' not in created_at:
        continue
    by_time.setdefault(created_at, []).append(d)

print(f"Total timestamps: {len(by_time)}")
for t, group in sorted(by_time.items()):
    if len(group) < 2:
        continue
    print(f"Timestamp: {t}")
    for d in group:
        print(f"  ID: {d['id']} | Score: {d['score']}")
        print(f"    Analysis: {d.get('text_analysis')}")
        audit = d.get('audit_details') or {}
        print(f"    QA: upsell={audit.get('upsell_score')}, cross_sales={audit.get('cross_sales_score')}, loyalty={audit.get('loyalty_score')}, live_service={audit.get('live_service_score')}")
    print("=" * 80)
