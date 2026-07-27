import json

log_path = r'C:\Users\Aziz\.gemini\antigravity\brain\2374903e-05e1-4d3f-b247-a0ee3e55109c\.system_generated\logs\transcript.jsonl'

with open(log_path, 'r', encoding='utf-8') as f:
    for line in f:
        try:
            data = json.loads(line)
            source = data.get('source', '')
            step = data.get('step_index', 0)
            
            # Print only user inputs or relevant steps from the end of history
            if step > 8400:
                if source == 'USER_EXPLICIT':
                    print(f"Step {step} (User): {data.get('content')}")
                elif data.get('type') == 'PLANNER_RESPONSE' and data.get('status') == 'DONE':
                    print(f"Step {step} (Model): {data.get('content')[:150]}...")
        except Exception as e:
            pass
