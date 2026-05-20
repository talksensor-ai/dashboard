"""Check existing transcript and GigaAM version."""
import paramiko
import time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('81.29.139.211', username='root', password='nIyjYRinAVKAPL23bk6f')

test = '''
import os

# Check existing transcript
f = "/root/talk/pipeline/2026-04-22_17-18-22-04-2026_transcript.txt"
if os.path.exists(f):
    with open(f, "r", encoding="utf-8") as fh:
        lines = fh.readlines()
    print(f"Existing transcript: {len(lines)} lines")
    for l in lines[:10]:
        print(f"  {l.rstrip()}")
else:
    print("No existing transcript!")

# Check GigaAM version and model details
import gigaam
print(f"\\nGigaAM version: {gigaam.__version__}")
print(f"GigaAM location: {gigaam.__file__}")

# Check available models
import torch
print(f"\\nPyTorch: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"GPU: {torch.cuda.get_device_name()}")
    
# Check pip version of gigaam
import subprocess
r = subprocess.run(["pip", "show", "gigaam"], capture_output=True, text=True)
print(f"\\npip show gigaam:\\n{r.stdout}")
'''

sftp = ssh.open_sftp()
with sftp.file('/root/talk/_check_gigaam.py', 'w') as f:
    f.write(test)
sftp.close()

_, out, err = ssh.exec_command(
    'cd /root/talk && source .venv/bin/activate && python3 _check_gigaam.py 2>&1'
)
time.sleep(15)
print(out.read().decode('utf-8', 'replace'))
ssh.close()
