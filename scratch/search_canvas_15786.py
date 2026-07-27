import re

canvas_path = 'e:/talk/scratch/daily_canvas_2026-05-21_mac.txt'

with open(canvas_path, 'r', encoding='utf-8', errors='ignore') as f:
    lines = f.readlines()

print(f"Loaded {len(lines)} lines.")

# Look for timecodes around 15786
found = []
for i, line in enumerate(lines):
    match = re.search(r'\[(\d+)\s*-\s*(\d+)\]', line)
    if match:
        start = int(match.group(1))
        end = int(match.group(2))
        if 15500 <= start <= 16500:
            found.append((i+1, start, end, line.strip()))

print(f"Found {len(found)} timecodes around 15786:")
for item in found[:30]:
    print(f"Line {item[0]}: {item[3]}")
