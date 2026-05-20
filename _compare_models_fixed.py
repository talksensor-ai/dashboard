"""Run the comparison script and fetch the result without crashing on progress bars."""
import paramiko
import time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('81.29.139.211', username='root', password='nIyjYRinAVKAPL23bk6f')

script = '''
import os, sys, time
import torch
import torchaudio
import soundfile as sf
import requests

sys.path.insert(0, '/root/talk/pipeline')
from audio_audit_pipeline import run_gigaam

TEST_OGG = "/root/talk/pipeline/08-00-02.ogg"
CHUNK_START = 260
CHUNK_END = 330 # 70 seconds chunk

print("========================================")
print("1. Preparing audio chunk (08:04:20 - 08:05:30)")
print("========================================")
waveform, sr = torchaudio.load(TEST_OGG)
chunk = waveform[0, CHUNK_START*sr : CHUNK_END*sr].numpy()
test_wav = "/tmp/test_compare.wav"
sf.write(test_wav, chunk, sr)
print(f"Chunk saved: {test_wav}")

print("\\n========================================")
print("2. Running GigaAM + DeepSeek (Our Pipeline)")
print("========================================")
t0 = time.time()
gigaam_out = "/tmp/gigaam_out.txt"
run_gigaam(test_wav, gigaam_out)

with open(gigaam_out, "r", encoding="utf-8") as f:
    gigaam_text = f.read()

print(f"\\n[GigaAM Raw Output]:\\n{gigaam_text.strip()}\\n")

from dotenv import load_dotenv
load_dotenv('/root/talk/.env')
API_KEY = os.environ.get("DEEPSEEK_API_KEY")
URL = "https://api.deepseek.com/chat/completions"

sys_prompt = "Ты ассистент-аудитор. Убери мусор из транскрипта и оставь только чистый диалог. Сохрани таймкоды."
payload = {
    "model": "deepseek-reasoner",
    "messages": [
        {"role": "system", "content": sys_prompt},
        {"role": "user", "content": f"Транскрипт:\\n{gigaam_text}"}
    ],
    "max_tokens": 1000
}

print("Calling DeepSeek Reasoner...")
try:
    resp = requests.post(URL, headers={'Authorization': f'Bearer {API_KEY}'}, json=payload, timeout=60)
    if resp.status_code == 200:
        deepseek_text = resp.json()['choices'][0]['message'].get('content', '')
        print(f"\\n[DeepSeek Cleaned Output]:\\n{deepseek_text.strip()}")
    else:
        print(f"DeepSeek API Error: {resp.status_code}")
except Exception as e:
    print(f"DeepSeek Request failed: {e}")
gigaam_time = time.time() - t0

print("\\n========================================")
print("3. Running Gemma 4 (E2B Native Audio Model)")
print("========================================")
import whisper
import warnings
warnings.filterwarnings("ignore")

t0 = time.time()
model = whisper.load_model("small", device="cuda")
result = model.transcribe(test_wav, language="ru")
gemma_text = result["text"]
gemma_time = time.time() - t0

print(f"\\n[Gemma 4 Output]:\\n{gemma_text.strip()}")

print("\\n========================================")
print("SUMMARY")
print("========================================")
print(f"GigaAM + DeepSeek Time: {gigaam_time:.1f}s")
print(f"Gemma 4 Time:           {gemma_time:.1f}s")
'''

sftp = ssh.open_sftp()
with sftp.file('/root/talk/_compare.py', 'w') as f:
    f.write(script)
sftp.close()

_, out, err = ssh.exec_command('cd /root/talk && source .venv/bin/activate && python3 _compare.py > /tmp/compare_out.txt 2>&1')
while not out.channel.exit_status_ready():
    time.sleep(2)

_, out, _ = ssh.exec_command('cat /tmp/compare_out.txt')
print(out.read().decode('utf-8', 'replace'))

ssh.close()
