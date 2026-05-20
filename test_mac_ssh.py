import paramiko
import sys

def test_ssh():
    host = '100.123.93.21'
    user = 'ai'
    pw = '1234'
    
    print(f"Connecting to {host} as {user}...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        ssh.connect(host, port=22, username=user, password=pw, timeout=10)
        print("Connected successfully!")
        
        commands = [
            "mkdir -p ~/talk_project",
            "touch ~/talk_project/test_file.txt",
            "echo 'Hello from Antigravity' > ~/talk_project/test_file.txt",
            "ls -la ~/talk_project",
            "cat ~/talk_project/test_file.txt",
            "rm ~/talk_project/test_file.txt",
            "rmdir ~/talk_project"
        ]
        
        for cmd in commands:
            print(f"\nRunning: {cmd}")
            stdin, stdout, stderr = ssh.exec_command(cmd)
            out = stdout.read().decode().strip()
            err = stderr.read().decode().strip()
            if out: print(out)
            if err: print(f"Error: {err}")
            
        ssh.close()
    except Exception as e:
        print(f"Failed to connect: {e}")

if __name__ == "__main__":
    test_ssh()
