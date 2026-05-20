import paramiko
import sys
import re

with open(r'e:\talk\pipeline\daily_cache_worker.py', 'r', encoding='utf-8') as f:
    code = f.read()

# patch timestamp_to_seconds
new_func = '''def timestamp_to_seconds(ts_str):
    """Converts 'HH-MM-SS' or 'HH-MM-DD-MM-YYYY' to absolute seconds from midnight."""
    parts = ts_str.split('-')
    h = int(parts[0])
    m = int(parts[1])
    s = int(parts[2]) if len(parts) == 3 else 0
    return h * 3600 + m * 60 + s'''

old_func_regex = r'def timestamp_to_seconds\(ts_str\):[\s\S]*?return h \* 3600 \+ m \* 60 \+ s'
patched_code = re.sub(old_func_regex, new_func, code)

with open(r'e:\talk\pipeline\daily_cache_worker_22_april.py', 'w', encoding='utf-8') as f:
    f.write(patched_code)

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('81.29.139.211', port=22, username='root', password='nIyjYRinAVKAPL23bk6f')
sftp = ssh.open_sftp()
sftp.put(r'e:\talk\pipeline\daily_cache_worker_22_april.py', '/root/talk/pipeline/daily_cache_worker_22_april.py')
sftp.close()

print("Uploaded script. Executing ...")
cmd = """cd /root/talk/pipeline && stdbuf -oL /root/talk/.venv/bin/python3 daily_cache_worker_22_april.py 2026-04-22"""
stdin, stdout, stderr = ssh.exec_command(cmd)

# Print lines as they arrive
for line in iter(stdout.readline, ''):
    sys.stdout.write(line)
    sys.stdout.flush()

err = stderr.read().decode()
if err:
    print("STDERR:")
    print(err)

ssh.close()
