"""Replace first chunk in daily canvas with re-transcribed version."""
import re

CANVAS = r'e:\talk\daily_canvas_2026-04-16.txt'
NEW_TRANSCRIPT = r'e:\talk\2026-04-16_08-00-01_transcript.txt'

# Read new transcript
with open(NEW_TRANSCRIPT, 'r', encoding='utf-8') as f:
    new_text = f.read()

# Read canvas
with open(CANVAS, 'r', encoding='utf-8') as f:
    canvas = f.read()

# The first chunk starts at the beginning and ends before "=== ЧАНК: 09-00-01.ogg"
# Apply time shift of 28801 seconds to new transcript timestamps
def shift_timestamps(text, shift):
    def replace_ts(m):
        s = int(m.group(1)) + shift
        e = int(m.group(2)) + shift
        return f'[{s} - {e}]'
    return re.sub(r'\[(\d+)\s*-\s*(\d+)\]', replace_ts, text)

shifted_new = shift_timestamps(new_text, 28801)

# Build new first chunk header
header = "\\n\\n=== ЧАНК: 08-00-01.ogg (Сдвиг: 28801 сек) ===\\n\\n"

# Find where second chunk starts
second_chunk_marker = "\\n\\n=== ЧАНК: 09-00-01.ogg"
idx = canvas.find(second_chunk_marker)

if idx == -1:
    print("ERROR: Second chunk marker not found!")
    exit(1)

# Replace first chunk
new_canvas = header + shifted_new + canvas[idx:]

with open(CANVAS, 'w', encoding='utf-8') as f:
    f.write(new_canvas)

print(f"Canvas updated! First chunk replaced.")
print(f"Old size: {len(canvas)}, New size: {len(new_canvas)}")
