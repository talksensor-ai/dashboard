import json
import re

log_path = r"C:\Users\Aziz\.gemini\antigravity\brain\f68e40c1-9d71-46f7-a3b5-91dc71a7d854\.system_generated\logs\transcript_full.jsonl"
gemini_text = ""
with open(log_path, 'r', encoding='utf-8') as f:
    for line in f:
        try:
            data = json.loads(line)
            if 'Вот с такой идеей' in data.get('content', ''):
                gemini_text = data['content']
        except Exception as e:
            pass

with open(r"E:\Talk\gemini_full.txt", "w", encoding="utf-8") as out:
    out.write(gemini_text)
print(f"Extracted {len(gemini_text)} characters.")
