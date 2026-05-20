import paramiko, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('81.29.139.211', username='root', password='nIyjYRinAVKAPL23bk6f')
_, out, _ = ssh.exec_command('tail -n 50 /tmp/compare_full.log | tr "\\r" "\\n" | tail -n 20')
print(out.read().decode('utf-8','replace'))
ssh.close()
