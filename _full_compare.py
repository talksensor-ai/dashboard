"""Download and cache Gemma 4 E2B model, then run full comparison test."""
import paramiko
import time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('81.29.139.211', username='root', password='nIyjYRinAVKAPL23bk6f')

# Create the full test script
test_script = '''
import os, sys, time, gc
import torch
import torchaudio
import numpy as np
import librosa
import requests
import json

sys.path.insert(0, '/root/talk/pipeline')
from dotenv import load_dotenv
load_dotenv('/root/talk/.env')

TEST_OGG = "/root/talk/test_compare/19-00-27-04-2026.ogg"
RESULTS_DIR = "/root/talk/test_compare/results"
os.makedirs(RESULTS_DIR, exist_ok=True)

print(f"Test file: {TEST_OGG}")
waveform, sr = torchaudio.load(TEST_OGG)
duration = waveform.shape[1] / sr
print(f"Duration: {duration:.0f}s, SR: {sr}, Channels: {waveform.shape[0]}")

# ============================================================
# PIPELINE A: GigaAM + DeepSeek Reasoner
# ============================================================
print()
print("=" * 70)
print("PIPELINE A: GigaAM + DeepSeek Reasoner")
print("=" * 70)

t_start_a = time.time()

# Run GigaAM transcription
from audio_audit_pipeline import run_gigaam
gigaam_out = os.path.join(RESULTS_DIR, "gigaam_raw.txt")
if not os.path.exists(gigaam_out):
    run_gigaam(TEST_OGG, gigaam_out)
else:
    print(f"GigaAM output already exists, skipping...")

with open(gigaam_out, "r", encoding="utf-8") as f:
    gigaam_text = f.read()

gigaam_time = time.time() - t_start_a
print(f"[A] GigaAM transcription done in {gigaam_time:.1f}s")

# Count lines
gigaam_lines = [l.strip() for l in gigaam_text.split("\\n") if l.strip() and l.strip().startswith("[")]
print(f"[A] GigaAM raw output: {len(gigaam_lines)} timestamped lines")

# Now send FULL transcript to DeepSeek Reasoner for dialogue extraction
API_KEY = os.environ.get("DEEPSEEK_API_KEY")
URL = "https://api.deepseek.com/chat/completions"

iterator_prompt = """Ты профессиональный аудитор кофейни. Тебе дан транскрипт аудиозаписи из кофейни с таймкодами.

Задача: Найди и выдели ВСЕ диалоги заказа между бариста и клиентом.

Правила:
1. Сохрани оригинальные таймкоды [start - end]
2. Для каждого диалога укажи роли: БАРИСТА: и КЛИЕНТ:
3. Убери фоновый шум, музыку и нерелевантные звуки
4. Если слово неразборчиво, отметь как [неразб.]
5. Каждый диалог отдели строкой === ДИАЛОГ #N ===

Выдай ТОЛЬКО чистые диалоги с таймкодами. Не добавляй комментариев."""

print("[A] Sending to DeepSeek Reasoner...")
t_ds_start = time.time()
payload = {
    "model": "deepseek-reasoner",
    "messages": [
        {"role": "system", "content": iterator_prompt},
        {"role": "user", "content": gigaam_text}
    ],
    "max_tokens": 8000
}
headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

try:
    resp = requests.post(URL, headers=headers, json=payload, timeout=300)
    if resp.status_code == 200:
        ds_result = resp.json()["choices"][0]["message"].get("content", "")
        ds_time = time.time() - t_ds_start
        
        ds_out = os.path.join(RESULTS_DIR, "pipeline_a_deepseek_reasoner.txt")
        with open(ds_out, "w", encoding="utf-8") as f:
            f.write(ds_result)
        print(f"[A] DeepSeek Reasoner done in {ds_time:.1f}s")
    else:
        print(f"[A] DeepSeek API error: {resp.status_code} - {resp.text[:300]}")
        ds_result = "ERROR"
        ds_time = 0
except Exception as e:
    print(f"[A] DeepSeek request failed: {e}")
    ds_result = f"ERROR: {e}"
    ds_time = 0

total_a = time.time() - t_start_a
print(f"[A] Total Pipeline A time: {total_a:.1f}s")

# Free GPU for Gemma 4
import gigaam as _gigaam_module
# GigaAM caches model globally, need to clear
gc.collect()
torch.cuda.empty_cache()
print(f"[A] GPU memory freed. Used: {torch.cuda.memory_allocated()/1024/1024:.0f} MB")

# ============================================================
# PIPELINE B: Gemma 4 E2B (native audio transcription)
# ============================================================
print()
print("=" * 70)
print("PIPELINE B: Gemma 4 E2B (native audio)")
print("=" * 70)

t_start_b = time.time()

from transformers import AutoProcessor, AutoModelForMultimodalLM

MODEL_ID = "google/gemma-4-E2B-it"

print("[B] Loading Gemma 4 E2B model...")
t0 = time.time()
processor = AutoProcessor.from_pretrained(MODEL_ID)
model = AutoModelForMultimodalLM.from_pretrained(
    MODEL_ID,
    torch_dtype=torch.bfloat16,
    device_map="auto"
)
load_time = time.time() - t0
print(f"[B] Model loaded in {load_time:.1f}s")
print(f"[B] GPU memory: {torch.cuda.memory_allocated()/1024/1024:.0f} MB")

# Gemma 4 supports max 30 seconds of audio. We chunk into 30s segments.
# Load audio at 16kHz mono (as per model card)
audio_full, _ = librosa.load(TEST_OGG, sr=16000, mono=True)
total_duration = len(audio_full) / 16000

CHUNK_SEC = 30
all_transcripts = []

print(f"[B] Processing {total_duration:.0f}s in {CHUNK_SEC}s chunks...")

prompt_text = (
    "Transcribe the following speech segment in Russian into Russian text. "
    "Follow these specific instructions for formatting the answer:\\n"
    "* Only output the transcription, with no newlines.\\n"
    "* When transcribing numbers, write the digits.\\n"
    "* Include timestamps in format [MM:SS] at the start of each sentence."
)

chunk_idx = 0
pos = 0
t_transcribe = time.time()

while pos < len(audio_full):
    chunk_end = min(pos + CHUNK_SEC * 16000, len(audio_full))
    chunk = audio_full[pos:chunk_end]
    chunk_start_sec = pos / 16000
    chunk_end_sec = chunk_end / 16000
    
    chunk_idx += 1
    
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "audio", "audio": chunk},
                {"type": "text", "text": prompt_text},
            ],
        }
    ]
    
    inputs = processor.apply_chat_template(
        messages, tokenize=True, return_dict=True,
        return_tensors="pt", add_generation_prompt=True,
    ).to(model.device)
    
    input_len = inputs["input_ids"].shape[-1]
    
    with torch.no_grad():
        outputs = model.generate(**inputs, max_new_tokens=512)
    
    response = processor.decode(outputs[0][input_len:], skip_special_tokens=True)
    response = response.strip()
    
    if response:
        # Add absolute timestamp prefix
        abs_start = int(chunk_start_sec)
        abs_end = int(chunk_end_sec)
        all_transcripts.append(f"[{abs_start} - {abs_end}] {response}")
    
    if chunk_idx % 10 == 0 or chunk_idx <= 3:
        print(f"  Chunk {chunk_idx}: {chunk_start_sec:.0f}-{chunk_end_sec:.0f}s -> {len(response)} chars")
    
    pos = chunk_end

transcribe_time = time.time() - t_transcribe
total_b = time.time() - t_start_b

# Save result
gemma_result = "\\n".join(all_transcripts)
gemma_out = os.path.join(RESULTS_DIR, "pipeline_b_gemma4.txt")
with open(gemma_out, "w", encoding="utf-8") as f:
    f.write(f"Gemma 4 E2B Transcription: {TEST_OGG}\\n")
    f.write(f"Total chunks: {chunk_idx}, Duration: {total_duration:.0f}s\\n")
    f.write("=" * 60 + "\\n\\n")
    f.write(gemma_result)

print(f"[B] Gemma 4 transcription done in {transcribe_time:.1f}s ({chunk_idx} chunks)")
print(f"[B] Total Pipeline B time: {total_b:.1f}s")

# ============================================================
# FINAL COMPARISON
# ============================================================
print()
print("=" * 70)
print("FINAL COMPARISON")
print("=" * 70)

# Pipeline A summary
print(f"\\n--- Pipeline A: GigaAM + DeepSeek Reasoner ---")
print(f"GigaAM time:     {gigaam_time:.1f}s")
print(f"DeepSeek time:   {ds_time:.1f}s")
print(f"Total:           {total_a:.1f}s")
print(f"Raw lines:       {len(gigaam_lines)}")
if ds_result and ds_result != "ERROR":
    ds_lines = [l for l in ds_result.split("\\n") if l.strip()]
    print(f"Clean dialogues: {len(ds_lines)} lines")

# Pipeline B summary
gemma_lines = [l for l in all_transcripts if l.strip()]
total_words_b = sum(len(l.split()) for l in gemma_lines)
print(f"\\n--- Pipeline B: Gemma 4 E2B ---")
print(f"Model load:      {load_time:.1f}s")
print(f"Transcribe:      {transcribe_time:.1f}s")
print(f"Total:           {total_b:.1f}s")
print(f"Output lines:    {len(gemma_lines)}")
print(f"Total words:     {total_words_b}")

# Show first 10 lines from each
print(f"\\n--- First 10 lines: Pipeline A (GigaAM raw) ---")
for l in gigaam_lines[:10]:
    print(f"  {l}")

print(f"\\n--- First 10 lines: Pipeline B (Gemma 4) ---")
for l in gemma_lines[:10]:
    print(f"  {l}")

# Save full DeepSeek Reasoner output preview
if ds_result and ds_result != "ERROR":
    print(f"\\n--- DeepSeek Reasoner output (first 2000 chars) ---")
    print(ds_result[:2000])

print(f"\\n\\nFull results saved to: {RESULTS_DIR}")
'''

sftp = ssh.open_sftp()
with sftp.file('/root/talk/_full_compare.py', 'w') as f:
    f.write(test_script)
sftp.close()

print("Running full comparison (this will take 10-20 minutes)...\n")
_, out, _ = ssh.exec_command(
    'cd /root/talk && source .venv/bin/activate && python3 _full_compare.py > /tmp/compare_full.log 2>&1'
)

# Monitor progress
last_size = 0
while not out.channel.exit_status_ready():
    time.sleep(15)
    _, check, _ = ssh.exec_command('wc -l /tmp/compare_full.log 2>/dev/null && tail -3 /tmp/compare_full.log 2>/dev/null')
    status = check.read().decode('utf-8', 'replace').strip()
    if status:
        print(f"  ... {status}")

# Get final output
_, out_final, _ = ssh.exec_command('cat /tmp/compare_full.log')
time.sleep(5)
result = out_final.read().decode('utf-8', 'replace')
print("\n" + result)

ssh.close()
