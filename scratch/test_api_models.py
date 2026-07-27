import paramiko

def run_cmd():
    host = '100.123.93.21'
    user = 'ai'
    pw = '1234'
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, username=user, password=pw)
    
    remote_script = """
import os, requests
from dotenv import load_dotenv
load_dotenv('/Users/ai/talk/.env')

key = os.environ.get('DEEPSEEK_API_KEY', '')
url = 'https://api.deepseek.com/v1/models'
headers = {'Authorization': f'Bearer {key}'}

try:
    resp = requests.get(url, headers=headers, timeout=10)
    print('V1 Models Status:', resp.status_code)
    if resp.status_code == 200:
        models = resp.json()
        print('Available models:')
        for m in models.get('data', []):
            print('  -', m.get('id'))
    else:
        print('Response:', resp.text[:500])
except Exception as e:
    print('Error:', e)
"""
    
    sftp = ssh.open_sftp()
    with sftp.file('/Users/ai/talk/temp_check_models.py', 'w') as f:
        f.write(remote_script)
    sftp.close()
    
    stdin, stdout, stderr = ssh.exec_command('/Users/ai/talk/.venv/bin/python /Users/ai/talk/temp_check_models.py')
    print("--- STDOUT ---")
    print(stdout.read().decode('utf-8'))
    print("--- STDERR ---")
    print(stderr.read().decode('utf-8'))
    
    ssh.exec_command('rm /Users/ai/talk/temp_check_models.py')
    ssh.close()

if __name__ == '__main__':
    run_cmd()
