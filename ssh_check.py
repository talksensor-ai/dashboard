import paramiko
import sys

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('81.29.139.211', port=22, username='root', password='nIyjYRinAVKAPL23bk6f', timeout=30, banner_timeout=200, auth_timeout=30)

stdin, stdout, stderr = ssh.exec_command('ls -la /root/talk')
print(stdout.read().decode())

stdin, stdout, stderr = ssh.exec_command('ls -la /root/talk/pipeline')
print(stdout.read().decode())

ssh.close()
