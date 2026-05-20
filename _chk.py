import paramiko, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('81.29.139.211', username='root', password='nIyjYRinAVKAPL23bk6f')
_, out, _ = ssh.exec_command('ps aux | grep _full_compare | grep -v grep; echo "---"; wc -l /tmp/compare_full.log; echo "---LAST20---"; tail -20 /tmp/compare_full.log | grep -v "Loading weights"')
import time; time.sleep(3)
print(out.read().decode('utf-8','replace'))
ssh.close()
