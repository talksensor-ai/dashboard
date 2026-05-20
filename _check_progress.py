"""Check current progress of the comparison test."""
import paramiko
import time
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('81.29.139.211', username='root', password='nIyjYRinAVKAPL23bk6f')

_, out, _ = ssh.exec_command('wc -l /tmp/compare_full.log 2>/dev/null; echo "---TAIL---"; tail -30 /tmp/compare_full.log 2>/dev/null; echo "---PS---"; ps aux | grep _full_compare | grep -v grep')
time.sleep(3)
print(out.read().decode('utf-8', 'replace'))

ssh.close()
