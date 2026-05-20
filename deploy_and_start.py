"""Deploy updated files to server and start test_day_runner in screen."""
import paramiko
import os
import sys
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

SERVER = os.environ["SERVER_IP"]
USER = os.environ["SERVER_USER"]
PASS = os.environ["SERVER_PASS"]
BASE = os.path.dirname(__file__)

# Files to upload (local path -> remote path)
FILES = {
    "pipeline/test_day_runner.py": "/root/talk/pipeline/test_day_runner.py",
    "pipeline/daily_cache_worker.py": "/root/talk/pipeline/daily_cache_worker.py",
    "pipeline/glossary.json": "/root/talk/pipeline/glossary.json",
    "pipeline/audio_audit_pipeline.py": "/root/talk/pipeline/audio_audit_pipeline.py",
    "pipeline/push_to_supabase.py": "/root/talk/pipeline/push_to_supabase.py",
    "docs/iterator_prompt.md": "/root/talk/docs/iterator_prompt.md",
    "docs/qa_prompt.md": "/root/talk/docs/qa_prompt.md",
    ".env": "/root/talk/.env",
}

print(f"Connecting to {SERVER}...")
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(SERVER, username=USER, password=PASS)

# Create dirs
print("Creating directories...")
ssh.exec_command("mkdir -p /root/talk/pipeline /root/talk/docs")

# Upload files
sftp = ssh.open_sftp()
for local_rel, remote in FILES.items():
    local = os.path.join(BASE, local_rel)
    if os.path.exists(local):
        print(f"  Uploading {local_rel} -> {remote}")
        sftp.put(local, remote)
    else:
        print(f"  [SKIP] {local_rel} not found locally")
sftp.close()
print("All files uploaded!")

# Check Python and dependencies
print("\nChecking Python environment...")
_, out, err = ssh.exec_command("python3 --version && pip3 list 2>/dev/null | grep -iE 'yadisk|requests|dotenv|paramiko|supabase|gigaam'")
print(out.read().decode())

# Install missing deps if needed
print("Installing/updating dependencies...")
_, out, err = ssh.exec_command("pip3 install -q python-dotenv requests yadisk supabase 2>&1 | tail -5")
print(out.read().decode())
errs = err.read().decode()
if errs:
    print(f"Warnings: {errs[:200]}")

# Start the runner in screen (persists after disconnect)
print("\nStarting test_day_runner in screen session 'testday'...")
# Kill any existing session
ssh.exec_command("screen -S testday -X quit 2>/dev/null")
import time
time.sleep(1)

# Start new screen session with the runner
_, out, err = ssh.exec_command(
    "cd /root/talk && screen -dmS testday python3 pipeline/test_day_runner.py"
)
time.sleep(2)

# Verify it's running
_, out, err = ssh.exec_command("screen -ls && echo '---' && ps aux | grep test_day_runner | grep -v grep")
result = out.read().decode()
print(result)

if "testday" in result:
    print("\n[OK] test_day_runner is running in screen session 'testday'")
    print("To attach: ssh root@81.29.139.211 then: screen -r testday")
    print("To detach: Ctrl+A, D")
else:
    print("\n[ERROR] Failed to start. Checking logs...")
    _, out, err = ssh.exec_command("cd /root/talk && python3 pipeline/test_day_runner.py 2>&1 | head -20")
    time.sleep(5)
    print(out.read().decode())
    print(err.read().decode())

ssh.close()
print("\nDone! Script is running on server.")
