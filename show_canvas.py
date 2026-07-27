import re
with open('/Users/ai/talk/pipeline/daily_canvas_2026-05-19.txt', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for line in lines:
    m = re.match(r'\[(\d+)\s*-\s*\d+\]', line.strip())
    if m:
        t = int(m.group(1))
        if 36000 <= t <= 36210:
            print(line.strip())
