"""Step 1: Check available files for April 27 + download Gemma 4 model."""
import paramiko
import time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('81.29.139.211', username='root', password='nIyjYRinAVKAPL23bk6f')

# 1. Check what audio from Apr 27 is on Yandex Disk
check_script = '''
import os, sys
sys.path.insert(0, '/root/talk/pipeline')
from dotenv import load_dotenv
load_dotenv('/root/talk/.env')
import yadisk

TOKEN = os.environ.get("YANDEX_TOKEN")
y = yadisk.YaDisk(token=TOKEN)

# List files in Apr 27 folder
target = "/Ак мечеть/2026-04-27"
try:
    items = list(y.listdir(target))
    oggs = sorted([i.name for i in items if i.type == 'file' and i.name.endswith('.ogg')])
    print(f"Files in {target}: {len(oggs)}")
    for f in oggs:
        item = next(i for i in items if i.name == f)
        print(f"  {f} ({item.size / 1024 / 1024:.1f} MB)")
except Exception as e:
    print(f"Error: {e}")
    # Try listing all date folders
    try:
        folders = list(y.listdir("/Ак мечеть"))
        dates = sorted([f.name for f in folders if f.type == 'dir'])
        print(f"Available dates: {dates}")
    except Exception as e2:
        print(f"Error listing folders: {e2}")
'''

sftp = ssh.open_sftp()
with sftp.file('/root/talk/_check_apr27.py', 'w') as f:
    f.write(check_script)
sftp.close()

print("=== Checking April 27 files on Yandex Disk ===\n")
_, out, _ = ssh.exec_command(
    'cd /root/talk && source .venv/bin/activate && python3 _check_apr27.py 2>&1'
)
while True:
    line = out.readline()
    if not line:
        break
    print(line.rstrip())

ssh.close()
