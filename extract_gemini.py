import json

log_path = r"C:\Users\Aziz\.gemini\antigravity\brain\f68e40c1-9d71-46f7-a3b5-91dc71a7d854\.system_generated\logs\transcript_full.jsonl"
with open(log_path, 'r', encoding='utf-8') as f:
    for line in f:
        try:
            data = json.loads(line)
            c = data.get('content', '')
            if 'Транскрипция Gemini' in c:
                print(f"{data.get('type')} - len: {len(c)}")
                if len(c) > 1000:
                    with open(r"E:\Talk\gemini_raw.txt", "w", encoding="utf-8") as out:
                        out.write(c)
        except Exception as e:
            pass
