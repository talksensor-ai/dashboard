"""
Download the latest audio from Yandex Disk (April 23, after 21:00)
and run GigaAM on the Linux server via SSH.
"""
import os
import sys
import paramiko
import yadisk
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

TOKEN = os.environ.get("YANDEX_TOKEN")
SERVER_IP = os.environ.get("SERVER_IP")
SERVER_USER = os.environ.get("SERVER_USER")
SERVER_PASS = os.environ.get("SERVER_PASS")

ya = yadisk.YaDisk(token=TOKEN)

# Target file on Yandex Disk
YA_PATH = "/Ак мечеть/2026-04-23/21-17-23-04-2026.ogg"
LOCAL_OGG = os.path.join(os.path.dirname(__file__), "21-17-23-04-2026.ogg")
REMOTE_OGG = "/root/talk/21-17-23-04-2026.ogg"
REMOTE_TXT = "/root/talk/21-17-23-04-2026_transcript.txt"

# Step 1: Download from Yandex Disk to local
if not os.path.exists(LOCAL_OGG):
    print(f"Downloading {YA_PATH} from Yandex Disk...")
    ya.download(YA_PATH, LOCAL_OGG)
    size_mb = os.path.getsize(LOCAL_OGG) / (1024 * 1024)
    print(f"Downloaded: {size_mb:.1f} MB")
else:
    size_mb = os.path.getsize(LOCAL_OGG) / (1024 * 1024)
    print(f"File already exists locally: {size_mb:.1f} MB")

# Step 2: SSH connect and upload
print(f"\nConnecting to server {SERVER_IP}...")
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(SERVER_IP, port=22, username=SERVER_USER, password=SERVER_PASS)

print(f"Uploading to {REMOTE_OGG}...")
sftp = ssh.open_sftp()
sftp.put(LOCAL_OGG, REMOTE_OGG)
sftp.close()
print("Upload complete!")

# Step 3: Run GigaAM on the server
print("\nRunning GigaAM transcription on server...")
cmd = f"""cd /root/talk/pipeline && /root/talk/.venv/bin/python3 -c "
import sys
sys.path.insert(0, '/root/talk/pipeline')
from audio_audit_pipeline import run_gigaam
run_gigaam('{REMOTE_OGG}', '{REMOTE_TXT}')
" """

stdin, stdout, stderr = ssh.exec_command(cmd, timeout=600)

# Stream output
for line in iter(stdout.readline, ''):
    sys.stdout.write(line)
    sys.stdout.flush()

err = stderr.read().decode()
if err:
    print("\nSTDERR:")
    print(err)

# Step 4: Read the transcript back
print("\n\n========== TRANSCRIPT ==========\n")
try:
    sftp2 = ssh.open_sftp()
    with sftp2.open(REMOTE_TXT, 'r') as f:
        transcript = f.read().decode('utf-8')
    sftp2.close()
    print(transcript)
    
    # Save locally too
    local_txt = LOCAL_OGG.replace('.ogg', '_transcript.txt')
    with open(local_txt, 'w', encoding='utf-8') as f:
        f.write(transcript)
    print(f"\n[+] Transcript saved locally: {local_txt}")
except Exception as e:
    print(f"Error reading transcript: {e}")

ssh.close()
