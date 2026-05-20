import os
import sys
import re

# add pipeline to sys path
sys.path.append(os.path.join('e:\\', 'talk', 'pipeline'))
from audio_audit_pipeline import run_gigaam

files = [
    '2026-04-22_17-18-22-04-2026.ogg',
    '2026-04-22_18-18-22-04-2026.ogg',
    '2026-04-22_19-18-22-04-2026.ogg',
    '2026-04-22_21-18-22-04-2026.ogg'
]

canvas_txt = "e:\\talk\\daily_canvas_2026-04-22.txt"

def timestamp_to_seconds(fname):
    # fname is like '2026-04-22_17-18-22-04-2026.ogg'
    base = fname.split('_')[1] # '17-18-22-04-2026.ogg'
    parts = base.split('-') # ['17', '18', '22', '04', '2026.ogg']
    h = int(parts[0])
    m = int(parts[1])
    s = 0 
    return h * 3600 + m * 60 + s

def shift_timestamps_in_text(raw_text, shift_sec):
    lines = raw_text.split('\n')
    new_lines = []
    pattern = re.compile(r'^\[(\d+)\s*-\s*(\d+)\](.*)$')
    for line in lines:
        match = pattern.match(line.strip())
        if match:
            start_s = int(match.group(1)) + shift_sec
            end_s = int(match.group(2)) + shift_sec
            text = match.group(3)
            new_lines.append(f"[{start_s} - {end_s}]{text}")
        else:
            if line.strip():
                new_lines.append(line)
    return "\n".join(new_lines)


with open(canvas_txt, 'w', encoding='utf-8') as canvas_file:
    for f in files:
        ogg_path = os.path.join('e:\\', 'talk', f)
        txt_path = ogg_path.replace('.ogg', '_transcript.txt')
        if not os.path.exists(txt_path):
            print(f"Running GigaAM for {f}...")
            # We enforce sys.stdout to flush so we can see progress in the logs
            sys.stdout.flush()
            run_gigaam(ogg_path, txt_path)
        else:
            print(f"Transcript already found: {txt_path}, skipping GigaAM")
        
        with open(txt_path, 'r', encoding='utf-8') as tr:
            raw_text = tr.read()
            
        shift_s = timestamp_to_seconds(f)
        shifted = shift_timestamps_in_text(raw_text, shift_s)
        
        canvas_file.write(f"\n\n=== ЧАНК: {f} (Сдвиг: {shift_s} сек) ===\n\n")
        canvas_file.write(shifted)

print("Canvas built: " + canvas_txt)
