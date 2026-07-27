import paramiko
import sys

def run_cmd(cmd):
    host = '100.123.93.21'
    user = 'ai'
    pw = '1234'
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, username=user, password=pw)
    
    print(f"Running on Mac Mini: {cmd}")
    stdin, stdout, stderr = ssh.exec_command(cmd)
    
    out = stdout.read().decode('utf-8', errors='ignore').strip()
    err = stderr.read().decode('utf-8', errors='ignore').strip()
    
    if out:
        print("--- STDOUT ---")
        print(out)
    if err:
        print("--- STDERR ---")
        print(err)
        
    ssh.close()

if __name__ == "__main__":
    # We want to run a python command on Mac Mini to check the .env file
    # Let's run a script that checks key existence in ~/talk/.env
    cmd = "/Users/ai/talk/.venv/bin/python -c \"import os; from dotenv import load_dotenv; load_dotenv('/Users/ai/talk/.env'); [print(k, bool(v)) for k, v in os.environ.items() if 'API_KEY' in k or 'TOKEN' in k or 'GEMINI' in k]\""
    run_cmd(cmd)
