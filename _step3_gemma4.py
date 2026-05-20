"""Fix torchaudio + download Gemma 4 E2B model."""
import paramiko
import time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('81.29.139.211', username='root', password='nIyjYRinAVKAPL23bk6f')

# Fix torchaudio
print("=== Fixing torchaudio ===")
_, out, _ = ssh.exec_command(
    'cd /root/talk && source .venv/bin/activate && pip install -U torchaudio 2>&1 | tail -5'
)
while not out.channel.exit_status_ready():
    time.sleep(2)
print(out.read().decode('utf-8', 'replace'))

# Download Gemma 4 E2B model (this will take a while — ~5GB)
print("\n=== Downloading Gemma 4 E2B model (pre-caching) ===")
download_script = '''
import os
os.environ["HF_HOME"] = "/root/.cache/huggingface"

from transformers import AutoProcessor, AutoModelForMultimodalLM
import torch

MODEL_ID = "google/gemma-4-E2B-it"

print("Downloading processor...")
processor = AutoProcessor.from_pretrained(MODEL_ID)
print("Processor downloaded!")

print("Downloading model (this will take a few minutes)...")
model = AutoModelForMultimodalLM.from_pretrained(
    MODEL_ID,
    torch_dtype=torch.bfloat16,
    device_map="auto"
)
print(f"Model downloaded and loaded!")
print(f"Model device: {model.device}")
print(f"Model dtype: {model.dtype}")
print(f"GPU memory used: {torch.cuda.memory_allocated()/1024/1024:.0f} MB")

# Quick smoke test
del model
del processor
torch.cuda.empty_cache()
print("Model unloaded, cache cleared.")
print("GEMMA4_READY=true")
'''

sftp = ssh.open_sftp()
with sftp.file('/root/talk/_download_gemma4.py', 'w') as f:
    f.write(download_script)
sftp.close()

_, out, _ = ssh.exec_command(
    'cd /root/talk && source .venv/bin/activate && python3 _download_gemma4.py 2>&1'
)

while True:
    line = out.readline()
    if not line:
        break
    print(line.rstrip())

exit_code = out.channel.recv_exit_status()
print(f"\nExit code: {exit_code}")
ssh.close()
