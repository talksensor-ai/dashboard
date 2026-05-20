import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('81.29.139.211', port=22, username='root', password='nIyjYRinAVKAPL23bk6f')

code = """
import os
import torch
import torchaudio
import gigaam
import time

def normalize_and_transcribe(audio_path):
    print(f"Normalizing {audio_path}...")
    waveform, sr = torchaudio.load(audio_path)
    # Normalize to max amplitude 0.9
    max_val = waveform.abs().max()
    if max_val > 0:
        waveform = waveform / max_val * 0.9
    
    tmp_path = audio_path.replace('.ogg', '_norm.wav')
    torchaudio.save(tmp_path, waveform, sr)
    
    print(f"Saved normalized audio to {tmp_path}")
    print("Loading GigaAM...")
    model = gigaam.load_model('v3_e2e_rnnt', device='cuda')
    print("Transcribing...")
    t0 = time.time()
    res = model.transcribe_longform(tmp_path, word_timestamps=True)
    t1 = time.time()
    
    words = []
    for seg in res.segments:
        if seg.words:
            for w in seg.words:
                words.append(w.text)
                
    text = " ".join(words)
    print(f"Time: {t1-t0:.1f}s")
    print(f"Result (first 500 chars): {text[:500]}")
    
normalize_and_transcribe('/root/talk/pipeline/2026-04-22_17-18-22-04-2026.ogg')
"""

with open(r'e:\talk\test_norm.py', 'w', encoding='utf-8') as f:
    f.write(code)

sftp = ssh.open_sftp()
sftp.put(r'e:\talk\test_norm.py', '/root/talk/pipeline/test_norm.py')
sftp.close()

stdin, stdout, stderr = ssh.exec_command('cd /root/talk/pipeline && /root/talk/.venv/bin/python3 test_norm.py')
print(stdout.read().decode())
print("STDERR: ", stderr.read().decode())
