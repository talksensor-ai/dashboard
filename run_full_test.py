import paramiko, os, sys
sys.stdout.reconfigure(encoding='utf-8')
from dotenv import load_dotenv
load_dotenv('e:/talk/.env')

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(os.environ['SERVER_IP'], username=os.environ['SERVER_USER'], password=os.environ['SERVER_PASS'])

test_script = '''
import sys, time, requests, json, re
sys.path.insert(0, "/root/talk/pipeline")
from audio_audit_pipeline import run_gigaam

audio_path = "/root/talk/2026-04-24_13-00-24-04-2026.ogg"
output_txt = "/root/talk/transcript_13_00_blind.txt"

print("1. RUNNING GIGAAM WITH 6s OVERLAP...")
run_gigaam(audio_path, output_txt)

print("\\n2. PREPARING DEEPSEEK CALL...")
with open(output_txt, 'r', encoding='utf-8') as f:
    transcript = f.read()

# Load full prompt and glossary
with open("/root/talk/docs/iterator_prompt.md", "r", encoding="utf-8") as f:
    base_prompt = f.read()

with open("/root/talk/pipeline/glossary.json", "r", encoding="utf-8") as f:
    glossary = f.read()

sys_content = base_prompt + "\\n\\nГЛОССАРИЙ:\\n" + glossary + "\\n\\n=== ТРАНСКРИПТ КОФЕЙНИ ===\\n\\n" + transcript

# We target the specific dialogue around 7:54 (474s) to verify all fixes
user_prompt = "Найди диалог заказа, который начался СТРОГО ПОСЛЕ 400 секунды. Выдай только его текст."

payload = {
    "model": "deepseek-reasoner",
    "messages": [
        {"role": "system", "content": sys_content},
        {"role": "user", "content": user_prompt}
    ],
    "max_tokens": 4000
}

import os
API_KEY = os.environ.get("DEEPSEEK_API_KEY")
headers = {
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {API_KEY}'
}

print("3. WAITING FOR DEEPSEEK REASONER...")
resp = requests.post("https://api.deepseek.com/chat/completions", json=payload, headers=headers)
if resp.status_code == 200:
    data = resp.json()['choices'][0]['message']
    print("\\n=== REASONING CONTENT ===")
    print(data.get('reasoning_content', ''))
    print("\\n=== FINAL DIALOGUE OUTPUT ===")
    print(data.get('content', ''))
else:
    print(f"DeepSeek Error {resp.status_code}: {resp.text}")
'''

sftp = c.open_sftp()
with sftp.file('/root/talk/_run_full_test.py', 'w') as f:
    f.write(test_script)
sftp.close()

print("Running end-to-end test on server (GigaAM + DeepSeek)...")
_, o, e = c.exec_command('/root/talk/.venv/bin/python3 /root/talk/_run_full_test.py', timeout=600)

for line in o:
    print(line.rstrip())

err = e.read().decode().strip()
if err:
    for l in err.split('\n'):
        if 'warning' not in l.lower() and 'UserWarning' not in l and l.strip():
            print(f'ERR: {l}')

c.close()
