import os
os.environ["PATH"] = os.environ.get("PATH", "") + ":/opt/homebrew/bin"

import sys
sys.path.insert(0, '/Users/ai/talk/pipeline')

from audio_audit_pipeline import run_gigaam

audio_path = "/Users/ai/talk/2026-05-10_08-00-10-05-2026.ogg"
output_txt = "/Users/ai/talk/2026-05-10_08-00-10-05-2026_test_transcript.txt"

print(f"Starting run_gigaam on {audio_path}...")
run_gigaam(audio_path, output_txt)

print("\nFinished!")
if os.path.exists(output_txt):
    size = os.path.getsize(output_txt)
    print(f"Output file size: {size} bytes")
    print("Content preview:")
    with open(output_txt, 'r', encoding='utf-8') as f:
        print(f.read()[:1000])
else:
    print("Output file was NOT created!")
