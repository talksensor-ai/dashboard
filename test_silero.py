"""
Test Silero VAD on the critical 7:54 zone.
"""
import paramiko, os, sys
sys.stdout.reconfigure(encoding='utf-8')
from dotenv import load_dotenv
load_dotenv('e:/talk/.env')

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(os.environ['SERVER_IP'], username=os.environ['SERVER_USER'], password=os.environ['SERVER_PASS'])

test_script = '''
import torch
import torchaudio
import time

audio_path = "/root/talk/2026-04-24_13-00-24-04-2026.ogg"

print("Loading Silero VAD...")
model, utils = torch.hub.load(repo_or_dir='snakers4/silero-vad',
                              model='silero_vad',
                              force_reload=False)

(get_speech_timestamps, save_audio, read_audio, VADIterator, collect_chunks) = utils

print(f"Loading audio: {audio_path}")
wav = read_audio(audio_path, sampling_rate=16000)

print("\\nTesting with standard threshold (0.5):")
speech_timestamps = get_speech_timestamps(wav, model, sampling_rate=16000, threshold=0.5)

found = False
for ts in speech_timestamps:
    start_sec = ts['start'] / 16000
    end_sec = ts['end'] / 16000
    if 460 <= start_sec <= 500 or 460 <= end_sec <= 500:
        m1, s1 = divmod(int(start_sec), 60)
        m2, s2 = divmod(int(end_sec), 60)
        print(f"  [{m1}:{s1:02d} - {m2}:{s2:02d}] ({end_sec - start_sec:.1f}s)")
        if start_sec <= 474 <= end_sec:
            found = True

print(f"7:54 Detected at thr=0.5: {'YES' if found else 'NO'}")

print("\\nTesting with sensitive threshold (0.1):")
speech_timestamps_sensitive = get_speech_timestamps(wav, model, sampling_rate=16000, threshold=0.1, min_speech_duration_ms=100)

found_sensitive = False
for ts in speech_timestamps_sensitive:
    start_sec = ts['start'] / 16000
    end_sec = ts['end'] / 16000
    if 460 <= start_sec <= 500 or 460 <= end_sec <= 500:
        m1, s1 = divmod(int(start_sec), 60)
        m2, s2 = divmod(int(end_sec), 60)
        print(f"  [{m1}:{s1:02d} - {m2}:{s2:02d}] ({end_sec - start_sec:.1f}s)")
        if start_sec <= 474 <= end_sec:
            found_sensitive = True

print(f"7:54 Detected at thr=0.1: {'YES' if found_sensitive else 'NO'}")
'''

sftp = c.open_sftp()
with sftp.file('/root/talk/_test_silero.py', 'w') as f:
    f.write(test_script)
sftp.close()

print("Running Silero VAD test on server...")
_, o, e = c.exec_command(
    '/root/talk/.venv/bin/python3 /root/talk/_test_silero.py',
    timeout=120
)

for line in o:
    print(line.rstrip())

err = e.read().decode().strip()
if err:
    for l in err.split('\n'):
        if 'warning' not in l.lower() and 'UserWarning' not in l and l.strip():
            print(f'ERR: {l}')

c.close()
