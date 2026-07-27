import json

log_path = r'C:\Users\Aziz\.gemini\antigravity\brain\2374903e-05e1-4d3f-b247-a0ee3e55109c\.system_generated\logs\transcript.jsonl'

with open(log_path, 'r', encoding='utf-8') as f:
    for line in f:
        try:
            data = json.loads(line)
            source = data.get('source', '')
            if source == 'USER_EXPLICIT':
                content = data.get('content', '')
                print(f"Step {data.get('step_index')} (User): {content}")
            elif source == 'MODEL' and data.get('type') == 'PLANNER_RESPONSE':
                content = data.get('content', '')
                print(f"Step {data.get('step_index')} (Model): {content[:300]}...")
        except Exception as e:
            pass
