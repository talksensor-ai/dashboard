import paramiko, os
from dotenv import load_dotenv
load_dotenv("e:/talk/.env")

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("81.29.139.211", username="root", password=os.environ["SERVER_PASS"])

script = """
import gigaam
import inspect
model = gigaam.load_model('v3_e2e_rnnt')
print(inspect.getsource(model.transcribe_longform))
"""

_, o, _ = c.exec_command(f"/root/talk/.venv/bin/python3 -c '{script}'")
print(o.read().decode())
c.close()
