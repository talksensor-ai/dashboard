import paramiko, os
from dotenv import load_dotenv
load_dotenv("e:/talk/.env")

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("81.29.139.211", username="root", password=os.environ["SERVER_PASS"])

script = """
import os
import torch
from pyannote.audio import Pipeline
from gigaam import load_model

audio_path = '/root/talk/2026-04-24_13-00-24-04-2026.ogg'

print("Loading Pyannote VAD...")
vad = Pipeline.from_pretrained(
    "pyannote/voice-activity-detection",
    use_auth_token=os.environ.get("HF_TOKEN", "")
)

# Выкручиваем чувствительность на максимум
vad.instantiate({
    "onset": 0.05,
    "offset": 0.05,
    "min_speech_duration": 0.2,
    "min_silence_duration": 0.5
})

print("Running VAD...")
vad_segments = vad(audio_path)

segments = []
for segment in vad_segments.get_timeline().support():
    # Only keep segments around 460-500 seconds for our test
    if segment.start > 520:
        break
    if segment.end > 450:
        segments.append((segment.start, segment.end))

print(f"Found {len(segments)} segments in target region.")

print("Loading GigaAM...")
model = load_model('v3_e2e_rnnt', device='cuda')

print("Transcribing target segments...")
for start, end in segments:
    try:
        res = model.transcribe(audio_path, boundaries=[(start, end)], word_timestamps=False)
        print(f"[{start:.1f} - {end:.1f}] {res[0]}")
    except Exception as e:
        print(f"[{start:.1f} - {end:.1f}] ERROR: {e}")
"""

with open("e:/talk/test_custom_vad.py", "w") as f:
    f.write(script)

sftp = c.open_sftp()
with open("e:/talk/test_custom_vad.py", "rb") as local_f:
    with sftp.file('/root/talk/test_custom_vad.py', 'wb') as remote_f:
        remote_f.write(local_f.read())
sftp.close()

_, o, _ = c.exec_command("/root/talk/.venv/bin/python3 /root/talk/test_custom_vad.py")
print("Command started...")
