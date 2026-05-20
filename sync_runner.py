import paramiko, os
from dotenv import load_dotenv
load_dotenv("e:/talk/.env")

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("81.29.139.211", username="root", password=os.environ["SERVER_PASS"])

sftp = c.open_sftp()
with open("e:/talk/pipeline/test_day_runner.py", "rb") as local_f:
    with sftp.file('/root/talk/pipeline/test_day_runner.py', 'wb') as remote_f:
        remote_f.write(local_f.read())
sftp.close()

# Restart the screen session safely
# Send Ctrl+C to the screen session to generate report and save state
c.exec_command("screen -S testday -X stuff '^C'")
import time
time.sleep(5)
# Kill it if it didn't exit
c.exec_command("screen -S testday -X quit")
time.sleep(2)
# Start a new screen session with the runner
c.exec_command("cd /root/talk && screen -dmS testday /root/talk/.venv/bin/python3 pipeline/test_day_runner.py")

print("File synced and runner restarted in screen 'testday'")
c.close()
