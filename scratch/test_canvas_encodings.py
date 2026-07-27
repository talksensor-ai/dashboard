import sys

canvas_path = 'e:/talk/scratch/daily_canvas_2026-05-21_mac.txt'

encodings = ['utf-8', 'cp1251', 'koi8-r', 'utf-16', 'utf-16le', 'utf-16be', 'latin-1', 'cp866', 'mac-roman']

with open(canvas_path, 'rb') as f:
    raw_data = f.read()

print("File size:", len(raw_data), "bytes")

# Check sample bytes around line 1163
# We can find line 1163 starting index. Since lines are separated by \n or \r\n:
raw_lines = raw_data.split(b'\n')
print("Total raw lines:", len(raw_lines))

sample_line = raw_lines[1162] # 0-indexed line 1163
print("Raw line 1163 bytes:", sample_line)

for enc in encodings:
    try:
        decoded = sample_line.decode(enc)
        print(f"[{enc}] successfully decoded:")
        # Write to stdout with replacement to prevent console crashes
        sys.stdout.buffer.write(f"  {enc}: ".encode('utf-8'))
        sys.stdout.buffer.write(decoded.encode('utf-8'))
        sys.stdout.buffer.write(b'\n')
    except Exception as e:
        print(f"[{enc}] failed: {e}")
