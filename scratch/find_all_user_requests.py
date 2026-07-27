import json

log_path = r'C:\Users\Aziz\.gemini\antigravity\brain\2374903e-05e1-4d3f-b247-a0ee3e55109c\.system_generated\logs\transcript.jsonl'
output_path = r'e:\talk\scratch\user_requests_utf8.txt'

with open(log_path, 'r', encoding='utf-8') as f, open(output_path, 'w', encoding='utf-8') as out:
    for line in f:
        try:
            data = json.loads(line)
            if data.get('source') == 'USER_EXPLICIT' or data.get('type') == 'USER_INPUT':
                content = data.get('content', '')
                if isinstance(content, dict):
                    content = json.dumps(content, ensure_ascii=False)
                out.write(f"Step {data.get('step_index')} (User):\n{content.strip()}\n")
                out.write("="*60 + "\n")
        except Exception:
            pass

print("Saved user requests to", output_path)
