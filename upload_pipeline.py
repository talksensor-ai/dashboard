"""Upload updated audio_audit_pipeline.py to server."""
import paramiko, os, sys
sys.stdout.reconfigure(encoding='utf-8')
from dotenv import load_dotenv
load_dotenv('e:/talk/.env')

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(os.environ['SERVER_IP'], username=os.environ['SERVER_USER'], password=os.environ['SERVER_PASS'])

sftp = c.open_sftp()
sftp.put('e:/talk/pipeline/audio_audit_pipeline.py', '/root/talk/pipeline/audio_audit_pipeline.py')
sftp.close()
c.close()
print("Successfully uploaded audio_audit_pipeline.py to the server!")
