
import sys
sys.path.insert(0, '/root/talk/pipeline')
from audio_audit_pipeline import run_gigaam
import time

audio = '/root/talk/2026-04-24_13-00-24-04-2026.ogg'
txt = '/root/talk/test_13_00.txt'

print("Running GigaAM with updated parameters...")
run_gigaam(audio, txt)

print("Checking lines around 475s (7:55)...")
import re
with open(txt, 'r', encoding='utf-8') as f:
    for line in f:
        match = re.search(r'\[(\d+) -', line)
        if match:
            start_time = int(match.group(1))
            if 460 <= start_time <= 520:
                print(line.strip())
