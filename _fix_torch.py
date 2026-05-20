"""Fix CUDA/torch stack properly."""
import paramiko
import time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('81.29.139.211', username='root', password='nIyjYRinAVKAPL23bk6f')

# Reinstall torch stack for CUDA 12.8
print("=== Reinstalling PyTorch for CUDA 12.8 ===")
_, out, _ = ssh.exec_command(
    'cd /root/talk && source .venv/bin/activate && '
    'pip install torch==2.10.0 torchvision==0.25.0 torchaudio==2.10.0 --index-url https://download.pytorch.org/whl/cu128 2>&1 | tail -10'
)
while not out.channel.exit_status_ready():
    time.sleep(5)
print(out.read().decode('utf-8', 'replace'))

# Verify torch works
print("\n=== Verifying PyTorch ===")
_, out2, _ = ssh.exec_command(
    'cd /root/talk && source .venv/bin/activate && python3 -c "import torch; print(torch.__version__); print(torch.cuda.is_available()); print(torch.cuda.get_device_name())"'
)
time.sleep(10)
print(out2.read().decode('utf-8', 'replace'))

# Verify transformers can load
print("=== Verifying transformers ===")
_, out3, _ = ssh.exec_command(
    'cd /root/talk && source .venv/bin/activate && python3 -c "from transformers import AutoProcessor, AutoModelForMultimodalLM; print(\'OK\')"'
)
time.sleep(10)
print(out3.read().decode('utf-8', 'replace'))

ssh.close()
print("Done!")
