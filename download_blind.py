"""Download the blind transcript from the server."""
import paramiko, os, sys
sys.stdout.reconfigure(encoding='utf-8')
from dotenv import load_dotenv
load_dotenv('e:/talk/.env')

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(os.environ['SERVER_IP'], username=os.environ['SERVER_USER'], password=os.environ['SERVER_PASS'])

sftp = c.open_sftp()
sftp.get('/root/talk/transcript_13_00_blind.txt', 'e:/talk/transcript_13_00_blind.txt')
sftp.close()
c.close()
print("Downloaded transcript_13_00_blind.txt")
