"""Check faster-whisper on server."""
import paramiko, os
from dotenv import load_dotenv
load_dotenv("e:/talk/.env")

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("81.29.139.211", username="root", password=os.environ["SERVER_PASS"])

_, o, _ = c.exec_command("/root/talk/.venv/bin/pip show faster-whisper 2>/dev/null")
print("[PIP SHOW]")
print(o.read().decode())

_, o, _ = c.exec_command("cat /root/talk/pipeline/audio_audit_pipeline.py | grep -i whisper")
print("[EXISTING WHISPER CODE]")
print(o.read().decode())

c.close()
