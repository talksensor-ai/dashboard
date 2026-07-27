import json
import os

with open('e:\\talk\\scratch\\results_2026-05-21.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

dialogues = []
for res in data.get('results', []):
    eval_data = res.get('evaluation')
    if eval_data:
        dialogues.append(eval_data)

output_path = 'e:\\talk\\scratch\\restore.json'
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump({'dialogues': dialogues}, f, ensure_ascii=False)

print(f"Created restore.json with {len(dialogues)} dialogues.")
