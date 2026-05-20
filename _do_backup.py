import paramiko, os, time
from dotenv import load_dotenv

load_dotenv("e:/talk/.env")

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(os.environ["SERVER_IP"], username=os.environ["SERVER_USER"], password=os.environ["SERVER_PASS"], timeout=30, banner_timeout=200)

print("1. Creating tar archive on the server (excluding .venv and __pycache__)...")
cmd = "tar --exclude='talk/.venv' --exclude='*/__pycache__*' -czf /root/talk_backup.tar.gz -C /root talk"
stdin, stdout, stderr = ssh.exec_command(cmd)

# Wait for command to finish
exit_status = stdout.channel.recv_exit_status()
if exit_status != 0:
    print("Error creating archive:", stderr.read().decode())
else:
    print("Archive created successfully on the server!")

print("2. Downloading archive to Windows (E:\\talk_server_backup\\talk_backup.tar.gz)...")
os.makedirs("E:\\talk_server_backup", exist_ok=True)
sftp = ssh.open_sftp()
sftp.get("/root/talk_backup.tar.gz", "E:\\talk_server_backup\\talk_backup.tar.gz")
sftp.close()

print("3. Cleaning up archive on server...")
ssh.exec_command("rm /root/talk_backup.tar.gz")
ssh.close()

print("DONE! The backup is saved in E:\\talk_server_backup\\talk_backup.tar.gz")
