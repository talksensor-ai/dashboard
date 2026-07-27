import json

log_path = r'C:\Users\Aziz\.gemini\antigravity\brain\2374903e-05e1-4d3f-b247-a0ee3e55109c\.system_generated\logs\transcript.jsonl'

steps = []
with open(log_path, 'r', encoding='utf-8') as f:
    for line in f:
        try:
            data = json.loads(line)
            steps.append(data)
        except Exception:
            pass

print(f"Total steps: {len(steps)}")
print("--- LAST 20 USER/MODEL/SYSTEM STEPS ---")
count = 0
for step in reversed(steps):
    source = step.get('source', '')
    step_type = step.get('type', '')
    content = step.get('content', '')
    # If content is a dict, convert to string
    if isinstance(content, dict):
        content = json.dumps(content, ensure_ascii=False)
    
    if source in ('USER_EXPLICIT', 'MODEL', 'SYSTEM'):
        print(f"Step {step.get('step_index')} | Source: {source} | Type: {step_type}")
        print(f"Content: {content[:300]}")
        print("-" * 50)
        count += 1
        if count >= 30:
            break
