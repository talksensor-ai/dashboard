import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('81.29.139.211', username='root', password='nIyjYRinAVKAPL23bk6f')

# read the local file
with open('_debug_gemma.py', 'r', encoding='utf-8') as f:
    script = f.read()

sftp = ssh.open_sftp()
with sftp.file('/root/talk/_debug_gemma.py', 'w') as f:
    f.write(script)
sftp.close()

_, out, _ = ssh.exec_command('cd /root/talk && source .venv/bin/activate && python3 _debug_gemma.py')

import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
while True:
    line = out.readline()
    if not line:
        break
    print(line.rstrip())

ssh.close()
