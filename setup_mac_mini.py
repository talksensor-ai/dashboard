import paramiko
import time

def setup_mac():
    host = '100.123.93.21'
    user = 'ai'
    pw = '1234'
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        ssh.connect(host, port=22, username=user, password=pw, timeout=10)
        print("Connected to Mac Mini.")
        
        print("Uploading brew_install.sh...")
        sftp = ssh.open_sftp()
        sftp.put('brew_install.sh', '/Users/ai/brew_install.sh')
        sftp.close()
        
        print("Installing Homebrew (running script and logging to file)...")
        install_cmd = 'NONINTERACTIVE=1 bash /Users/ai/brew_install.sh > /Users/ai/brew_install.log 2>&1'
        stdin, stdout, stderr = ssh.exec_command(install_cmd, get_pty=True)
        
        # Send password just in case it asks
        time.sleep(2)
        stdin.write(pw + "\n")
        stdin.flush()
        
        # Wait for completion
        while not stdout.channel.exit_status_ready():
            time.sleep(1)
        
        print(f"\nBrew installation finished with status: {stdout.channel.recv_exit_status()}")
        
        # Read log
        stdin, stdout, stderr = ssh.exec_command('cat /Users/ai/brew_install.log')
        print("--- INSTALL LOG ---")
        print(stdout.read().decode())
        print("--- END LOG ---")
        
        # Cleanup
        ssh.exec_command('rm /Users/ai/brew_install.sh')
        
        # After brew installation, we MUST add it to PATH
        print("Adding Brew to PATH...")
        add_to_path_cmd = '(echo; echo \'eval "$(/opt/homebrew/bin/brew shellenv)"\') >> /Users/ai/.zprofile'
        ssh.exec_command(add_to_path_cmd)
        
        # Now we can use the full path to brew for the rest of the session
        brew_path = "/opt/homebrew/bin/brew"

        # Step 2: Install basic tools
        print(f"\nInstalling FFmpeg and Python 3.12 using {brew_path}...")
        tools_cmd = f"{brew_path} install ffmpeg python@3.12"
        stdin, stdout, stderr = ssh.exec_command(tools_cmd, get_pty=True)
        # Sometime brew asks for password during install too
        while not stdout.channel.exit_status_ready():
            if stdout.channel.recv_ready():
                chunk = stdout.channel.recv(4096).decode('utf-8', errors='ignore')
                print(chunk, end="", flush=True)
                if "Password:" in chunk:
                    stdin.write(pw + "\n")
                    stdin.flush()
            time.sleep(0.5)
        
        # Step 3: Check versions
        print("\nVerifying installations:")
        for cmd in [f"{brew_path} --version", f"{brew_path} --prefix ffmpeg", "python3.12 --version"]:
            stdin, stdout, stderr = ssh.exec_command(f"eval \"$({brew_path} shellenv)\" && {cmd}")
            print(f"{cmd}: {stdout.readline().strip()}")

        ssh.close()
    except Exception as e:
        print(f"Setup failed: {e}")

if __name__ == "__main__":
    setup_mac()
