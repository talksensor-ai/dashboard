"""
Re-transcribe the first chunk (08-00-01.ogg) with updated VAD padding
and patch the daily canvas.
"""
import paramiko
import sys
import time

sys.stdout.reconfigure(encoding='utf-8')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('81.29.139.211', port=22, username='root', password='nIyjYRinAVKAPL23bk6f')

# 1. Check if the ogg file still exists
sftp = ssh.open_sftp()
files = sftp.listdir('/root/talk/pipeline')
ogg_file = '2026-04-16_08-00-01.ogg'
txt_file = '2026-04-16_08-00-01_transcript.txt'

if ogg_file not in [f for f in files]:
    print(f"OGG file {ogg_file} NOT found on server!")
    ssh.close()
    exit(1)

print(f"OGG file found: {ogg_file}")

# 2. Delete old transcript so GigaAM re-processes it
if txt_file in files:
    sftp.remove(f'/root/talk/pipeline/{txt_file}')
    print(f"Deleted old transcript: {txt_file}")

# 3. Run GigaAM on just this one file
print("\nRunning GigaAM with new VAD padding on first chunk...")
cmd = f"""cd /root/talk/pipeline && /root/talk/.venv/bin/python3 -c "
from audio_audit_pipeline import run_gigaam
run_gigaam('{ogg_file}', '{txt_file}')
print('DONE')
"
"""
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=120)

# Stream output
for line in iter(stdout.readline, ''):
    print(line.strip())

err = stderr.read().decode()
if err:
    print(f"Stderr: {err}")

# 4. Download new transcript
print("\nDownloading new transcript...")
sftp.get(f'/root/talk/pipeline/{txt_file}', f'e:\\talk\\{txt_file}')
print(f"Saved to e:\\talk\\{txt_file}")

# 5. Read it
with open(f'e:\\talk\\{txt_file}', 'r', encoding='utf-8') as f:
    new_transcript = f.read()

print(f"\nNew transcript ({len(new_transcript)} bytes):")
print(new_transcript[:1500])

sftp.close()
ssh.close()
