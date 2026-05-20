import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('81.29.139.211', username='root', password='nIyjYRinAVKAPL23bk6f')

# 1. Install gigaam official package
print("Installing official gigaam package...")
_, out, _ = ssh.exec_command('cd /root/talk && source .venv/bin/activate && pip install git+https://github.com/salute-developers/GigaAM.git#egg=gigaam[torch]')
print(out.read().decode('utf-8', 'replace'))

# 2. Upload local pipeline files
sftp = ssh.open_sftp()
with open('pipeline/emotion_analyzer.py', 'r', encoding='utf-8') as f:
    sftp.file('/root/talk/pipeline/emotion_analyzer.py', 'w').write(f.read())

with open('pipeline/daily_cache_worker.py', 'r', encoding='utf-8') as f:
    sftp.file('/root/talk/pipeline/daily_cache_worker.py', 'w').write(f.read())
sftp.close()

# 3. Create a test runner script
test_runner = """
import os, sys
sys.path.insert(0, '/root/talk/pipeline')
from daily_cache_worker import run_cache_iterator
import shutil

# We already have raw gigaam transcript for our 19-00 file
raw_txt = "/root/talk/test_compare/results/gigaam_raw.txt"
test_canvas = "/root/talk/test_compare/daily_canvas_2026-04-27.txt"

if not os.path.exists(test_canvas):
    # Mocking the daily canvas builder:
    # 19:00:00 = 19 * 3600 = 68400 seconds shift
    with open(raw_txt, "r", encoding="utf-8") as f:
        content = f.read()
        
    from daily_cache_worker import shift_timestamps_in_text
    shifted_content = shift_timestamps_in_text(content, 68400)
    
    with open(test_canvas, "w", encoding="utf-8") as f:
        f.write("=== ЧАНК: 19-00-27-04-2026.ogg (Сдвиг: 68400 сек) ===\\n\\n")
        f.write(shifted_content)

# We also need to copy the audio file to the folder where analyzer expects it
os.makedirs("/root/talk/test_compare/2026-04-27", exist_ok=True)
if not os.path.exists("/root/talk/test_compare/2026-04-27/19-00-27-04-2026.ogg"):
    shutil.copy2("/root/talk/test_compare/19-00-27-04-2026.ogg", "/root/talk/test_compare/2026-04-27/19-00-27-04-2026.ogg")

print("Running pipeline on single 1-hour file...")
run_cache_iterator(test_canvas, "2026-04-27", 8, root_path="/root/talk/test_compare")
"""

sftp = ssh.open_sftp()
sftp.file('/root/talk/test_emo_pipeline.py', 'w').write(test_runner)
sftp.close()

print("Running test pipeline...")
_, out2, _ = ssh.exec_command('cd /root/talk && source .venv/bin/activate && python3 test_emo_pipeline.py > /tmp/test_emo.log 2>&1')
import time
while not out2.channel.exit_status_ready():
    time.sleep(5)
    
_, log, _ = ssh.exec_command('tail -n 30 /tmp/test_emo.log')
print(log.read().decode('utf-8', 'replace'))

ssh.close()
