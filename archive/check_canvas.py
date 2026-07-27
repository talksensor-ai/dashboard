import json

# Raw dialogs
with open('/Users/ai/talk/pipeline/results_2026-05-19_raw.json', 'r') as f:
    raw = json.load(f)

# Evaluated results
with open('/Users/ai/talk/pipeline/results_2026-05-19.json', 'r') as f:
    evaluated = json.load(f)

for r in raw:
    print(f"\n{'='*60}")
    print(f"ДИАЛОГ #{r['idx']} ({r['min_time']}-{r['max_time']})")
    print(f"{'='*60}")
    print(r['text'])

print(f"\n\n{'='*60}")
print("QA ОЦЕНКИ")
print(f"{'='*60}")
for res in evaluated.get('results', []):
    idx = res['idx']
    ev = res['evaluation']
    qa = ev.get('qa_evaluation', ev)
    print(f"\nДиалог #{idx}:")
    print(f"  type: {ev.get('dialogue_type', '?')}")
    print(f"  cross_sales: {qa.get('cross_sales_score', '?')}")
    print(f"  upsell: {qa.get('upsell_score', '?')}")
    print(f"  christmas_tree: {qa.get('christmas_tree_score', '?')}")
    print(f"  promo: {qa.get('promo_score', '?')}")
    print(f"  loyalty: {qa.get('loyalty_score', '?')}")
    print(f"  order_dup: {qa.get('order_duplication_score', '?')}")
    print(f"  live_service: {qa.get('live_service_score', '?')}")
    print(f"  recommendation: {qa.get('recommendation', '?')}")
