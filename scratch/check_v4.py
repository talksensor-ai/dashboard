import json
with open('e:\\talk\\scratch\\v4_test.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

res = data['results'][0]['evaluation']
print('=== DIALOG ===')
for d in res['dialog']:
    print(f"{d['role']}: {d['text']}")

print('\n=== QA ===')
for k, v in res.get('qa_result', {}).items():
    if k != 'reasoning': print(f"{k}: {v}")
