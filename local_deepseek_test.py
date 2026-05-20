import os
import requests
import re
from dotenv import load_dotenv
import json

load_dotenv('e:/talk/.env')
API_KEY = os.environ.get("DEEPSEEK_API_KEY")

# Load real prompt
with open('e:/talk/docs/iterator_prompt.md', 'r', encoding='utf-8') as f:
    base_prompt = f.read()

# Load real glossary
with open('e:/talk/pipeline/glossary.json', 'r', encoding='utf-8') as f:
    glossary = f.read()

base_prompt += "\n\nГЛОССАРИЙ:\n" + glossary

# Load transcript
with open('e:/talk/transcript_13_00_blind.txt', 'r', encoding='utf-8') as f:
    transcript = f.read()

# Select the chunk around 7:54 (400-650 seconds) to give enough context
lines = transcript.split('\n')
chunk_lines = []
for line in lines:
    m = re.match(r'^\[(\d+)\s*-\s*(\d+)\]', line)
    if m:
        start = int(m.group(1))
        if 400 <= start <= 650:
            chunk_lines.append(line)

short_transcript = "\n".join(chunk_lines)

system_prompt = base_prompt + "\n\n=== ТРАНСКРИПТ КОФЕЙНИ ===\n\n" + short_transcript

user_prompt = "Найди диалог заказа, который начался СТРОГО ПОСЛЕ 400 секунды. Выдай только его текст."

print("Запрашиваем DeepSeek Reasoner с полным промптом и обновленным глоссарием...")

payload = {
    "model": "deepseek-reasoner",
    "messages": [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ],
    "max_tokens": 4000
}

headers = {
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {API_KEY}'
}

resp = requests.post("https://api.deepseek.com/chat/completions", json=payload, headers=headers)
if resp.status_code == 200:
    data = resp.json()['choices'][0]['message']
    print("\n=== REASONING PROCESS ===")
    print(data.get('reasoning_content', ''))
    print("\n=== FINAL OUTPUT ===")
    print(data.get('content', ''))
else:
    print(f"Error {resp.status_code}: {resp.text}")
