import paramiko, os
from dotenv import load_dotenv
load_dotenv("e:/talk/.env")

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("81.29.139.211", username="root", password=os.environ["SERVER_PASS"])

_, o, _ = c.exec_command("cat /root/talk/2026-04-24_13-00-24-04-2026_transcript.txt | grep -E '\[4[0-9]{2} -|\[5[0-9]{2} -'")
print(o.read().decode())
c.close()
