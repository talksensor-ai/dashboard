import paramiko, os, sys
from dotenv import load_dotenv

load_dotenv('e:/talk/.env')
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(os.environ['SERVER_IP'], username=os.environ['SERVER_USER'], password=os.environ['SERVER_PASS'])

sftp = c.open_sftp()
# Upload updated files
sftp.put('e:/talk/pipeline/daily_cache_worker.py', '/root/talk/pipeline/daily_cache_worker.py')
sftp.put('e:/talk/pipeline/emotion_analyzer.py', '/root/talk/pipeline/emotion_analyzer.py')
sftp.put('e:/talk/pipeline/push_to_supabase.py', '/root/talk/pipeline/push_to_supabase.py')
sftp.put('e:/talk/docs/qa_prompt.md', '/root/talk/docs/qa_prompt.md')
sftp.close()

stdin, stdout, stderr = c.exec_command('cd /root/talk && source .venv/bin/activate && screen -dmS pipeline_25 python3 pipeline/daily_cache_worker.py 2026-04-25')
print("Pipeline started correctly in background (screen -r pipeline_25)!")
c.close()
