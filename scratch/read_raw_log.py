import json

log_path = r'C:\Users\Aziz\.gemini\antigravity\brain\2374903e-05e1-4d3f-b247-a0ee3e55109c\.system_generated\logs\transcript.jsonl'

with open(log_path, 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        if any(w in line.lower() for w in ['флеш', 'про', 'v4', 'deepseek', 'gemini']):
            try:
                data = json.loads(line)
                source = data.get('source', '')
                step = data.get('step_index', 0)
                content = data.get('content', '')
                print(f"Line {i} | Step {step} | Source {source} | Snippet: {content[:100]}")
            except Exception:
                print(f"Line {i} has match but error decoding json")
