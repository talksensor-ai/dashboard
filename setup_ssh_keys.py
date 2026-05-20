import os
import subprocess
import paramiko

# 1. Paths
home = os.path.expanduser("~")
ssh_dir = os.path.join(home, ".ssh")
priv_key = os.path.join(ssh_dir, "id_rsa")
pub_key = os.path.join(ssh_dir, "id_rsa.pub")

# Ensure .ssh dir exists locally
os.makedirs(ssh_dir, exist_ok=True)

# 2. Generate SSH key pair if not exists
if not os.path.exists(priv_key):
    print("Generating RSA SSH key pair...")
    subprocess.run(["ssh-keygen", "-t", "rsa", "-b", "4096", "-f", priv_key, "-N", ""], check=True)
    print("Keys generated successfully.")
else:
    print("SSH key pair already exists.")

# Read public key
with open(pub_key, "r") as f:
    pub_key_content = f.read().strip()

# 3. Connect to Mac Mini and install public key
mac_ip = "100.123.93.21"
mac_user = "ai"
mac_pass = "1234"

print(f"Connecting to Mac Mini ({mac_ip}) via SSH to install the key...")
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(mac_ip, username=mac_user, password=mac_pass)

# Commands to setup .ssh and authorized_keys on Mac
setup_commands = f"""
mkdir -p ~/.ssh
chmod 700 ~/.ssh
echo "{pub_key_content}" >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
echo "SSH Key successfully added to authorized_keys on Mac Mini."
"""

stdin, stdout, stderr = ssh.exec_command(setup_commands)
print(stdout.read().decode())
err = stderr.read().decode()
if err:
    print("Errors:", err)

ssh.close()
print("Done! You can now connect to the Mac Mini without a password.")
