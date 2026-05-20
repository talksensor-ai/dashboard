"""
Test: bypass VAD entirely. Split audio into fixed 25-sec chunks
and feed each to GigaAM .transcribe() directly.
Check if 'Dobryy den' at 7:54 appears.
"""
import paramiko, os, sys
sys.stdout.reconfigure(encoding='utf-8')
from dotenv import load_dotenv
load_dotenv('e:/talk/.env')

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(os.environ['SERVER_IP'], username=os.environ['SERVER_USER'], password=os.environ['SERVER_PASS'])

test_script = '''
import sys, os, time, torch, torchaudio
sys.path.insert(0, "/root/GigaAM")
import gigaam

audio_path = "/root/talk/2026-04-24_13-00-24-04-2026.ogg"

# Load model
print("Loading GigaAM...")
model = gigaam.load_model("v3_e2e_rnnt", device="cuda")
print("Model loaded!")

# Load full audio
print(f"Loading audio: {audio_path}")
waveform, sr = torchaudio.load(audio_path)
if sr != 16000:
    waveform = torchaudio.functional.resample(waveform, sr, 16000)
    sr = 16000

# Only test the critical zone: 7:00 - 9:00 (420-540 sec)
# Split into 25-sec chunks
chunk_sec = 25
start_sec = 420
end_sec = 540

print(f"\\nTesting zone {start_sec//60}:{start_sec%60:02d} - {end_sec//60}:{end_sec%60:02d}")
print(f"Chunk size: {chunk_sec}s\\n")

# Save temp chunks and transcribe each
import tempfile, soundfile as sf
import numpy as np

audio_np = waveform[0].numpy()  # mono

for chunk_start in range(start_sec, end_sec, chunk_sec):
    chunk_end = min(chunk_start + chunk_sec, end_sec)
    
    # Extract chunk
    s_idx = chunk_start * sr
    e_idx = chunk_end * sr
    chunk = audio_np[s_idx:e_idx]
    
    # Save to temp file
    tmp_path = f"/tmp/chunk_{chunk_start}.wav"
    sf.write(tmp_path, chunk, sr)
    
    # Transcribe (no VAD!)
    try:
        result = model.transcribe(tmp_path, word_timestamps=True)
        m_s, s_s = divmod(chunk_start, 60)
        m_e, s_e = divmod(chunk_end, 60)
        
        if result.words:
            words_text = []
            for w in result.words:
                abs_start = chunk_start + w.start
                words_text.append((abs_start, abs_start + (w.end - w.start), w.text))
            
            for ws, we, wt in words_text:
                wm_s, ws_s = divmod(int(ws), 60)
                wm_e, ws_e = divmod(int(we), 60)
                print(f"  [{wm_s}:{ws_s:02d}] {wt}")
        else:
            text = result.text if hasattr(result, "text") else str(result)
            if text and text.strip():
                print(f"  [{m_s}:{s_s:02d} - {m_e}:{s_e:02d}] {text.strip()}")
            else:
                print(f"  [{m_s}:{s_s:02d} - {m_e}:{s_e:02d}] (silence)")
    except Exception as ex:
        print(f"  [{chunk_start}s] Error: {ex}")
    
    os.remove(tmp_path)

print("\\nDone!")
'''

sftp = c.open_sftp()
with sftp.file('/root/talk/_test_no_vad.py', 'w') as f:
    f.write(test_script)
sftp.close()

print("Running no-VAD test on 7:00-9:00 zone...")
_, o, e = c.exec_command(
    '/root/talk/.venv/bin/python3 /root/talk/_test_no_vad.py',
    timeout=120
)

for line in o:
    print(line.rstrip())

err = e.read().decode().strip()
if err:
    for l in err.split('\n'):
        if 'warning' not in l.lower() and 'UserWarning' not in l and 'torch' not in l.lower() and 'matmul' not in l and 'pyannote' not in l and l.strip():
            print(f'ERR: {l}')

c.close()
