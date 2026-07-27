import re

canvas_path = '/Users/ai/talk/daily_canvas_2026-05-21_cumulative.txt'
print("Checking canvas file:", canvas_path)

with open(canvas_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

ranges = [0, 0, 0] # <3745, 3745-10000, >10000
examples = []

for idx, l in enumerate(lines):
    m = re.match(r'^\[(\d+)\s*-\s*(\d+)\]', l.strip())
    if m:
        t = int(m.group(1))
        if t < 3745:
            ranges[0] += 1
        elif t <= 10000:
            ranges[1] += 1
            if len(examples) < 10:
                examples.append((t, l.strip()))
        else:
            ranges[2] += 1

print(f"Total lines parsed with timestamps: {sum(ranges)}")
print(f"Before 3745: {ranges[0]} lines")
print(f"Between 3745 and 10000: {ranges[1]} lines")
print(f"Above 10000: {ranges[2]} lines")

print("\nFirst 10 lines between 3745 and 10000:")
for t, text in examples:
    print(f"  [{t}] {text}")
