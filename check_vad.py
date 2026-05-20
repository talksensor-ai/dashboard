import paramiko
import sys

sys.stdout.reconfigure(encoding='utf-8')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('81.29.139.211', port=22, username='root', password='nIyjYRinAVKAPL23bk6f')

# Add 0.5s padding before each VAD segment start
# Change: start = max(0, segment.start)
# To:     start = max(0, segment.start - 0.5)
print("Patching vad_utils.py...")
stdin, stdout, stderr = ssh.exec_command(
    "sed -i 's/start = max(0, segment.start)/start = max(0, segment.start - 0.5)/' /root/GigaAM/gigaam/vad_utils.py"
)
err = stderr.read().decode()
if err:
    print(f"Error: {err}")
else:
    print("OK: Added 0.5s pre-padding to VAD segments")

# Verify
print("\nVerification:")
stdin, stdout, stderr = ssh.exec_command("grep 'segment.start' /root/GigaAM/gigaam/vad_utils.py")
print(stdout.read().decode())

ssh.close()
