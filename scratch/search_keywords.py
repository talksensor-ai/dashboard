import re

canvas_path = 'e:/talk/scratch/daily_canvas_2026-05-21_mac.txt'

with open(canvas_path, 'r', encoding='utf-8', errors='ignore') as f:
    lines = f.readlines()

print(f"Loaded {len(lines)} lines.")

# Search for matches of words
keywords = ["сэндвич", "курицей", "Мохито", "Анастасия", "Алина"]

for i, line in enumerate(lines):
    for kw in keywords:
        if kw.lower() in line.lower():
            print(f"Match for '{kw}' on Line {i+1}: {line.strip()}")
            break
