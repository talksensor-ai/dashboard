import json

log_path = r'C:\Users\Aziz\.gemini\antigravity\brain\2374903e-05e1-4d3f-b247-a0ee3e55109c\.system_generated\logs\transcript.jsonl'
output_path = r'e:\talk\scratch\history_readable.txt'

with open(log_path, 'r', encoding='utf-8') as f, open(output_path, 'w', encoding='utf-8') as out:
    for line in f:
        try:
            data = json.loads(line)
            source = data.get('source', '')
            step = data.get('step_index', 0)
            if source == 'USER_EXPLICIT':
                content = data.get('content', '')
                out.write(f"\nStep {step} (User):\n{content}\n")
            elif source == 'MODEL' and data.get('type') in ('PLANNER_RESPONSE', 'TEXT_RESPONSE'):
                content = data.get('content', '')
                out.write(f"\nStep {step} (Model):\n{content}\n")
        except Exception as e:
            pass

print("Done! Saved to e:\\talk\\scratch\\history_readable.txt")
