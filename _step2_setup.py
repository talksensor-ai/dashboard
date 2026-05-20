"""Step 2: Download April 27 evening audio + install Gemma 4 dependencies."""
import paramiko
import time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('81.29.139.211', username='root', password='nIyjYRinAVKAPL23bk6f')

# 1. Download test file
download_script = '''
import os, sys, time
sys.path.insert(0, '/root/talk/pipeline')
from dotenv import load_dotenv
load_dotenv('/root/talk/.env')
import yadisk
import numpy as np
import torchaudio

TOKEN = os.environ.get("YANDEX_TOKEN")
y = yadisk.YaDisk(token=TOKEN)

# Download evening file
target_file = "/Ак мечеть/2026-04-27/19-00-27-04-2026.ogg"
local_path = "/root/talk/test_compare/19-00-27-04-2026.ogg"

os.makedirs("/root/talk/test_compare", exist_ok=True)

if not os.path.exists(local_path):
    print(f"Downloading {target_file}...")
    t0 = time.time()
    y.download(target_file, local_path)
    print(f"Downloaded in {time.time()-t0:.1f}s ({os.path.getsize(local_path)/1024/1024:.1f} MB)")
else:
    print(f"Already exists: {local_path}")

# Check if the file has actual audio (not silence)
waveform, sr = torchaudio.load(local_path)
rms = float(np.sqrt(np.mean(waveform[0].numpy()**2)))
duration = waveform.shape[1] / sr
print(f"Duration: {duration:.0f}s, Channels: {waveform.shape[0]}, SR: {sr}, RMS: {rms:.6f}")

if rms < 0.001:
    print("WARNING: File appears to be SILENCE (RMS < 0.001)")
    print("Will fall back to working file from April 18")
    
    # Copy the known working file instead
    import shutil
    fallback = "/root/talk/pipeline/08-00-02.ogg"
    if os.path.exists(fallback):
        local_path = "/root/talk/test_compare/08-00-02_apr18.ogg"
        if not os.path.exists(local_path):
            shutil.copy2(fallback, local_path)
        waveform2, sr2 = torchaudio.load(local_path)
        rms2 = float(np.sqrt(np.mean(waveform2[0].numpy()**2)))
        duration2 = waveform2.shape[1] / sr2
        print(f"Fallback file: {local_path}")
        print(f"Duration: {duration2:.0f}s, Channels: {waveform2.shape[0]}, SR: {sr2}, RMS: {rms2:.6f}")
else:
    print("Audio has content! Using this file for comparison.")

print(f"FINAL_TEST_FILE={local_path}")
'''

sftp = ssh.open_sftp()
with sftp.file('/root/talk/_download_test.py', 'w') as f:
    f.write(download_script)
sftp.close()

print("=== Downloading test audio ===\n")
_, out, _ = ssh.exec_command(
    'cd /root/talk && source .venv/bin/activate && python3 _download_test.py 2>&1'
)
while True:
    line = out.readline()
    if not line:
        break
    print(line.rstrip())

# 2. Install Gemma 4 dependencies
print("\n\n=== Installing Gemma 4 dependencies ===\n")
_, out2, _ = ssh.exec_command(
    'cd /root/talk && source .venv/bin/activate && pip install -U transformers accelerate librosa torchvision 2>&1 | tail -15'
)
while not out2.channel.exit_status_ready():
    time.sleep(2)
print(out2.read().decode('utf-8', 'replace'))

ssh.close()
print("Done!")
