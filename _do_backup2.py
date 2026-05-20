import paramiko, os, time
from dotenv import load_dotenv

load_dotenv("e:/talk/.env")

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(os.environ["SERVER_IP"], username=os.environ["SERVER_USER"], password=os.environ["SERVER_PASS"], timeout=30, banner_timeout=200)

print("1. Creating tar archive for GigaAM...")
cmd = "tar -czf /root/GigaAM_backup.tar.gz -C /root GigaAM"
ssh.exec_command(cmd)
time.sleep(3) # Wait for small archive

print("2. Downloading GigaAM archive...")
sftp = ssh.open_sftp()
sftp.get("/root/GigaAM_backup.tar.gz", "E:\\talk_server_backup\\GigaAM_backup.tar.gz")
sftp.close()

print("3. Cleaning up...")
ssh.exec_command("rm /root/GigaAM_backup.tar.gz")
ssh.close()

print("DONE")
