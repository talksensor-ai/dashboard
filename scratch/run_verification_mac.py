import paramiko
import os

def run_remote():
    host = '100.123.93.21'
    user = 'ai'
    pw = '1234'
    
    local_script = r'e:\talk\scratch\test_remote_slice.py'
    remote_script = '/Users/ai/talk/test_remote_slice.py'
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        ssh.connect(host, username=user, password=pw, timeout=10)
        sftp = ssh.open_sftp()
        print(f"Uploading verification script...")
        sftp.put(local_script, remote_script)
        sftp.close()
        
        print("Running transcription test on Mac Mini...")
        # Run using virtual environment
        stdin, stdout, stderr = ssh.exec_command("/Users/ai/talk/.venv/bin/python /Users/ai/talk/test_remote_slice.py")
        out = stdout.read().decode('utf-8', errors='ignore').strip()
        err = stderr.read().decode('utf-8', errors='ignore').strip()
        
        if out:
            print("--- OUTPUT ---")
            print(out)
        if err:
            print("--- ERROR ---")
            print(err)
            
        ssh.close()
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    run_remote()
