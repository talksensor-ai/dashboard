import json

with open(r'C:\Users\Aziz\.gemini\antigravity\brain\2374903e-05e1-4d3f-b247-a0ee3e55109c\.system_generated\logs\transcript.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        try:
            data = json.loads(line)
            content = data.get('content', '')
            if not isinstance(content, str):
                continue
            lower_content = content.lower()
            if 'public.dialogs' in lower_content or 'create table' in lower_content or 'schema' in lower_content or 'migration' in lower_content or 'sql' in lower_content or 'база' in lower_content:
                print(f"Step {data.get('step_index')}: {content[:200]}...")
        except Exception as e:
            pass
