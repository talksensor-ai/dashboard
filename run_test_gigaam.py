import paramiko, os
from dotenv import load_dotenv
load_dotenv("e:/talk/.env")

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("81.29.139.211", username="root", password=os.environ["SERVER_PASS"])

script = """
import sys
sys.path.insert(0, '/root/talk/pipeline')
from audio_audit_pipeline import run_gigaam
import time

audio = '/root/talk/2026-04-24_13-00-24-04-2026.ogg'
txt = '/root/talk/test_13_00.txt'

print("Running GigaAM with updated parameters...")
run_gigaam(audio, txt)

print("Checking lines around 475s (7:55)...")
import re
with open(txt, 'r', encoding='utf-8') as f:
    for line in f:
        match = re.search(r'\[(\d+) -', line)
        if match:
            start_time = int(match.group(1))
            if 460 <= start_time <= 520:
                print(line.strip())
"""

# Stop test_day_runner if running
c.exec_command("screen -S testday -X quit")

# Run the test script
with open("e:/talk/test_gigaam_fix.py", "w") as f:
    f.write(script)

sftp = c.open_sftp()
with open("e:/talk/test_gigaam_fix.py", "rb") as local_f:
    with sftp.file('/root/talk/test_gigaam_fix.py', 'wb') as remote_f:
        remote_f.write(local_f.read())
sftp.close()

_, o, _ = c.exec_command("/root/talk/.venv/bin/python3 /root/talk/test_gigaam_fix.py")
print(o.read().decode())
c.close()
