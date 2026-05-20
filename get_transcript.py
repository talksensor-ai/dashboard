"""
Read the transcript from the server and save locally.
"""
import os
import paramiko
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

SERVER_IP = os.environ.get("SERVER_IP")
SERVER_USER = os.environ.get("SERVER_USER")
SERVER_PASS = os.environ.get("SERVER_PASS")

REMOTE_TXT = "/root/talk/21-17-23-04-2026_transcript.txt"
LOCAL_TXT = os.path.join(os.path.dirname(__file__), "21-17-23-04-2026_transcript.txt")

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(SERVER_IP, port=22, username=SERVER_USER, password=SERVER_PASS)

sftp = ssh.open_sftp()
try:
    sftp.get(REMOTE_TXT, LOCAL_TXT)
    print(f"Downloaded transcript to: {LOCAL_TXT}")
except Exception as e:
    print(f"Error: {e}")
    # Try to check if the file exists
    stdin, stdout, stderr = ssh.exec_command(f"ls -la {REMOTE_TXT}")
    print(stdout.read().decode())
    print(stderr.read().decode())
sftp.close()
ssh.close()
