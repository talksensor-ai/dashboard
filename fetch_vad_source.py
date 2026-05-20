import paramiko, os
from dotenv import load_dotenv
load_dotenv("e:/talk/.env")

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("81.29.139.211", username="root", password=os.environ["SERVER_PASS"])

script = """
import os
gigaam_dir = "/root/talk/.venv/lib/python3.10/site-packages/gigaam"
for root, dirs, files in os.walk(gigaam_dir):
    for f in files:
        if f.endswith(".py"):
            path = os.path.join(root, f)
            with open(path) as f_obj:
                content = f_obj.read()
            if "transcribe_longform" in content or "segment_audio" in content or "onset" in content:
                print(f"--- {path} ---")
                lines = content.split('\\n')
                for i, line in enumerate(lines):
                    if "def transcribe_longform" in line or "def segment" in line or "onset" in line:
                        start = max(0, i-5)
                        end = min(len(lines), i+15)
                        print("\\n".join(lines[start:end]))
                        print("...")
"""

_, o, _ = c.exec_command(f"/root/talk/.venv/bin/python3 -c '{script}'")
print(o.read().decode())
c.close()
