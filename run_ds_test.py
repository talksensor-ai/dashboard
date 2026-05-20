"""Run DeepSeek audit on the blind transcript and download results."""
import paramiko, os, sys
sys.stdout.reconfigure(encoding='utf-8')
from dotenv import load_dotenv
load_dotenv('e:/talk/.env')

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(os.environ['SERVER_IP'], username=os.environ['SERVER_USER'], password=os.environ['SERVER_PASS'])

ds_script = '''
import sys
sys.path.insert(0, "/root/talk/pipeline")
from audio_audit_pipeline import run_deepseek

txt_path = "/root/talk/transcript_13_00_blind.txt"
out_json = "/root/talk/audit_13_00.json"

with open(txt_path, "r", encoding="utf-8") as f:
    text = f.read()

print(f"Running DeepSeek Reasoner on {len(text)} chars of transcript...")
run_deepseek(text, out_json)
print("DeepSeek analysis complete!")
'''

sftp = c.open_sftp()
with sftp.file('/root/talk/_run_ds.py', 'w') as f:
    f.write(ds_script)
sftp.close()

print("Running DeepSeek on server...")
_, o, e = c.exec_command('/root/talk/.venv/bin/python3 /root/talk/_run_ds.py', timeout=300)
for line in o:
    print(line.rstrip())
err = e.read().decode().strip()
if err:
    print(f"ERR: {err}")

# Download results
sftp = c.open_sftp()
sftp.get('/root/talk/transcript_13_00_blind.txt', 'e:/talk/transcript_13_00_blind.txt')
sftp.get('/root/talk/audit_13_00.json', 'e:/talk/audit_13_00.json')
sftp.close()
c.close()

print("Downloaded transcript_13_00_blind.txt and audit_13_00.json")
