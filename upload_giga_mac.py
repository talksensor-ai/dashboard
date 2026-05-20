import os
import paramiko

def upload_giga():
    host = '100.123.93.21'
    user = 'ai'
    pw = '1234'
    local_path = r'e:\talk_server_backup\GigaAM'
    remote_path = '/Users/ai/GigaAM'
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, username=user, password=pw)
    
    sftp = ssh.open_sftp()
    
    print("Uploading GigaAM repository...")
    for root, dirs, files in os.walk(local_path):
        # Skip .git
        dirs[:] = [d for d in dirs if d not in ['.git']]
        
        for file in files:
            local_file = os.path.join(root, file)
            rel_path = os.path.relpath(local_file, local_path)
            remote_file = os.path.join(remote_path, rel_path).replace('\\', '/')
            
            # Ensure remote directory exists
            remote_dir = os.path.dirname(remote_file)
            ssh.exec_command(f'mkdir -p "{remote_dir}"')
            
            sftp.put(local_file, remote_file)
            
    sftp.close()
    
    print("Installing GigaAM in virtual environment...")
    # Install in editable mode
    install_cmd = f"cd {remote_path} && /Users/ai/talk/.venv/bin/pip install -e ."
    stdin, stdout, stderr = ssh.exec_command(install_cmd)
    print(stdout.read().decode())
    print(stderr.read().decode())
    
    ssh.close()
    print("GigaAM setup complete!")

if __name__ == "__main__":
    upload_giga()
