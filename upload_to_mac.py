import os
import paramiko

def upload_project():
    host = '100.123.93.21'
    user = 'ai'
    pw = '1234'
    local_path = r'e:\talk'
    remote_path = '/Users/ai/talk'
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, username=user, password=pw)
    
    sftp = ssh.open_sftp()
    
    for root, dirs, files in os.walk(local_path):
        # Skip excluded directories
        dirs[:] = [d for d in dirs if d not in [
            '.venv', '.venv312', '__pycache__', '.git', 'node_modules', 
            'dialogs_16', '.next', 'dist', 'build', '.turbo', '.contentlayer'
        ]]
        
        for file in files:
            if file.endswith(('.ogg', '.wav', '.tar.gz', '.mp3')):
                continue
            
            local_file = os.path.join(root, file)
            rel_path = os.path.relpath(local_file, local_path)
            remote_file = os.path.join(remote_path, rel_path).replace('\\', '/')
            
            # Ensure remote directory exists
            remote_dir = os.path.dirname(remote_file)
            ssh.exec_command(f'mkdir -p "{remote_dir}"')
            
            print(f"Uploading {rel_path}...")
            sftp.put(local_file, remote_file)
    
    sftp.close()
    ssh.close()
    print("Upload complete!")

if __name__ == "__main__":
    upload_project()
