"""Install deepfilternet on remote server."""
import paramiko
import time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('81.29.139.211', username='root', password='nIyjYRinAVKAPL23bk6f')

print("Installing deepfilternet in venv...")
_, out, err = ssh.exec_command(
    'cd /root/talk && source .venv/bin/activate && pip install deepfilternet 2>&1 | tail -30'
)

# Wait for completion
while not out.channel.exit_status_ready():
    time.sleep(2)
    
output = out.read().decode('utf-8', 'replace')
errors = err.read().decode('utf-8', 'replace')
print(output)
if errors.strip():
    print("STDERR:", errors)

# Verify install
print("\n--- Verification ---")
_, out2, _ = ssh.exec_command(
    'cd /root/talk && source .venv/bin/activate && python3 -c "from df.enhance import enhance, init_df; print(\'DeepFilterNet OK\')"'
)
time.sleep(10)
print(out2.read().decode('utf-8', 'replace'))

ssh.close()
print("Done!")
