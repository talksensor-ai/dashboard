canvas_path = 'e:/talk/scratch/daily_canvas_2026-05-21_mac.txt'

# Try reading in cp1251
try:
    with open(canvas_path, 'r', encoding='cp1251') as f:
        lines = f.readlines()
    print("Success reading with cp1251!")
    print("Lines 1130 to 1170:")
    for i in range(1130, min(1170, len(lines))):
        print(f"Line {i+1}: {lines[i].strip()}")
except Exception as e:
    print(f"cp1251 failed: {e}")
