"""Test GigaAM on a known working audio file."""
import paramiko
import time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('81.29.139.211', username='root', password='nIyjYRinAVKAPL23bk6f')

test = '''
import sys, time, os
sys.path.insert(0, '/root/talk/pipeline')
import torchaudio
import soundfile as sf
import numpy as np

TEST_OGG = "/root/talk/pipeline/08-00-02.ogg"
if not os.path.exists(TEST_OGG):
    print(f"File not found: {TEST_OGG}")
    sys.exit(1)

waveform, sr = torchaudio.load(TEST_OGG)

import gigaam
model = gigaam.load_model("v3_e2e_rnnt", device="cuda")

# Take a chunk from the middle (e.g. 5 minutes in)
start_sec = 300
end_sec = 320
s = start_sec * sr
e = end_sec * sr

if e <= waveform.shape[1]:
    chunk = waveform[0, s:e].numpy()
    rms = np.sqrt(np.mean(chunk**2))
    
    tmp = f"/tmp/test_chunk_known.wav"
    sf.write(tmp, chunk, sr)
    
    result = model.transcribe(tmp, word_timestamps=True)
    n_words = len(result.words) if result.words else 0
    text_preview = " ".join([w.text for w in result.words[:20]]) if result.words else "(empty)"
    
    print(f"[{start_sec:5d}-{end_sec:5d}s] RMS={rms:.6f} | {n_words:3d} words | {text_preview}")
else:
    print("File too short")
'''

sftp = ssh.open_sftp()
with sftp.file('/root/talk/_test_known.py', 'w') as f:
    f.write(test)
sftp.close()

print("Testing GigaAM on known file...\n")
_, out, err = ssh.exec_command(
    'cd /root/talk && source .venv/bin/activate && python3 _test_known.py 2>&1'
)

while True:
    line = out.readline()
    if not line:
        break
    print(line.rstrip())

exit_code = out.channel.recv_exit_status()
print(f"\nExit code: {exit_code}")
ssh.close()
