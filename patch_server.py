"""Patch audio_audit_pipeline.py on the server to improve short phrases."""
import paramiko, os
from dotenv import load_dotenv
load_dotenv("e:/talk/.env")

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("81.29.139.211", username="root", password=os.environ["SERVER_PASS"])

# Read remote file
sftp = c.open_sftp()
with sftp.file('/root/talk/pipeline/audio_audit_pipeline.py', 'r') as f:
    content = f.read().decode('utf-8')

# Replace the transcribe_longform call
old_call = "result = model.transcribe_longform(audio_path, word_timestamps=True)"
new_call = """result = model.transcribe_longform(
        audio_path, 
        word_timestamps=True,
        min_duration=5.0,
        max_duration=15.0,
        new_chunk_threshold=0.1
    )"""

if old_call in content:
    content = content.replace(old_call, new_call)
    with sftp.file('/root/talk/pipeline/audio_audit_pipeline.py', 'w') as f:
        f.write(content.encode('utf-8'))
    print("Successfully patched /root/talk/pipeline/audio_audit_pipeline.py!")
else:
    print("Could not find the old call. File might already be patched.")

sftp.close()

# We also need to restart the screen session because the test_day_runner imports this module
# But test_day_runner actually imports it fresh on each file maybe? No, it's imported at the top.
# Let's restart the testday screen.
print("Restarting testday screen...")
c.exec_command("screen -X -S testday quit")
c.exec_command("cd /root/talk && screen -dmS testday /root/talk/.venv/bin/python3 pipeline/test_day_runner.py")
print("Restarted!")

c.close()
