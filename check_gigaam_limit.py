import paramiko, os, sys
sys.stdout.reconfigure(encoding='utf-8')
from dotenv import load_dotenv
load_dotenv('e:/talk/.env')

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(os.environ['SERVER_IP'], username=os.environ['SERVER_USER'], password=os.environ['SERVER_PASS'])

_, o, _ = c.exec_command('grep "Too long wav file" -A 2 -B 2 -r /root/GigaAM/')
print(o.read().decode())
