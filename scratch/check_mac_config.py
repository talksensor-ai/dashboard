import paramiko
import sys

def run_cmd():
    host = '100.123.93.21'
    user = 'ai'
    pw = '1234'
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, username=user, password=pw)
    
    # Write a temporary python script on the Mac Mini to check key format and dns resolution
    remote_script = """
import os, socket
from dotenv import load_dotenv
load_dotenv('/Users/ai/talk/.env')

key = os.environ.get('DEEPSEEK_API_KEY', '')
print('DEEPSEEK_API_KEY length:', len(key))
if key:
    print('DEEPSEEK_API_KEY prefix:', key[:10])
    print('DEEPSEEK_API_KEY suffix:', key[-5:])

try:
    ip = socket.gethostbyname('api.deepseek.com')
    print('api.deepseek.com IP:', ip)
except Exception as e:
    print('DNS Error:', e)
"""
    
    # Write the script
    sftp = ssh.open_sftp()
    with sftp.file('/Users/ai/talk/temp_check.py', 'w') as f:
        f.write(remote_script)
    sftp.close()
    
    # Execute the script
    stdin, stdout, stderr = ssh.exec_command('/Users/ai/talk/.venv/bin/python /Users/ai/talk/temp_check.py')
    print("--- STDOUT ---")
    print(stdout.read().decode('utf-8'))
    print("--- STDERR ---")
    print(stderr.read().decode('utf-8'))
    
    # Clean up
    ssh.exec_command('rm /Users/ai/talk/temp_check.py')
    ssh.close()

if __name__ == '__main__':
    run_cmd()
