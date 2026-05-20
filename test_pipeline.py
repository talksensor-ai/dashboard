"""Run the updated pipeline with overlapping chunking on the 13:00 file."""
import paramiko, os, sys
sys.stdout.reconfigure(encoding='utf-8')
from dotenv import load_dotenv
load_dotenv('e:/talk/.env')

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(os.environ['SERVER_IP'], username=os.environ['SERVER_USER'], password=os.environ['SERVER_PASS'])

test_script = '''
import sys
sys.path.insert(0, "/root/talk/pipeline")

import audio_audit_pipeline as aap
audio_path = "/root/talk/2026-04-24_13-00-24-04-2026.ogg"
output_txt = "/root/talk/transcript_13_00_blind.txt"

print(f"Starting pipeline on {audio_path}...")
aap.run_gigaam(audio_path, output_txt)
print("Finished!")

# Quickly verify if 7:54 (474 sec) is present in the output
print("\\nChecking for 7:54 (474 sec) gap:")
found = False
with open(output_txt, "r", encoding="utf-8") as f:
    for line in f:
        if "474" in line or "475" in line or "Добрый день" in line:
            print("  " + line.strip())
            found = True
if not found:
    print("  'Добрый день' or 474-475 timestamp not found.")
'''

sftp = c.open_sftp()
with sftp.file('/root/talk/_test_blind_pipeline.py', 'w') as f:
    f.write(test_script)
sftp.close()

print("Running blind overlapping chunk transcription test (takes ~2 mins)...")
_, o, e = c.exec_command('/root/talk/.venv/bin/python3 /root/talk/_test_blind_pipeline.py', timeout=600)

for line in o:
    print(line.rstrip())

err = e.read().decode().strip()
if err:
    for l in err.split('\n'):
        if 'warning' not in l.lower() and 'UserWarning' not in l and l.strip():
            print(f'ERR: {l}')

c.close()
