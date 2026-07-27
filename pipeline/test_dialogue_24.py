import os
import sys
import json
import re
import requests
from dotenv import load_dotenv

# Load env
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(env_path)

API_KEY = os.environ.get("DEEPSEEK_API_KEY")
URL = "https://api.deepseek.com/chat/completions"
headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {API_KEY}'}

# Prompts
def load_prompt(fname):
    p = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'docs', fname)
    with open(p, 'r', encoding='utf-8') as f:
        return f.read()

iterator_prompt = load_prompt('iterator_prompt.md')

# Glossary
glossary_path = os.path.join(os.path.dirname(__file__), 'glossary.json')
with open(glossary_path, 'r', encoding='utf-8') as f:
    glossary_data = json.load(f)

glossary_md = "\n\n### ГЛОССАРИЙ И ПРАВИЛА НАПИСАНИЯ ПОЗИЦИЙ МЕНЮ:\n"
for category, items in glossary_data.items():
    if isinstance(items, list):
        glossary_md += f"- **{category}**: {', '.join(items)}\n"
    elif isinstance(items, dict):
        glossary_md += f"- **{category}**:\n"
        for k, v in items.items():
            glossary_md += f"  - «{k}» → «{v}»\n"
sys_content = iterator_prompt + glossary_md

# Canvas
CANVAS_FILE = "/Users/ai/talk/daily_canvas_2026-05-21_cumulative.txt"
with open(CANVAS_FILE, 'r', encoding='utf-8') as f:
    canvas_lines = f.readlines()

parsed_canvas = []
for line in canvas_lines:
    match = re.match(r'\[(\d+)\s*-\s*(\d+)\]', line.strip())
    if match:
        parsed_canvas.append({
            "start": int(match.group(1)),
            "end": int(match.group(2)),
            "text": line.strip()
        })

def get_window(after_second, size=10000):
    window_lines = []
    total_chars = 0
    found_start = False
    for entry in parsed_canvas:
        if entry["start"] >= after_second:
            found_start = True
        if found_start:
            window_lines.append(entry["text"])
            total_chars += len(entry["text"]) + 1
            if total_chars >= size:
                break
    return "\n".join(window_lines)

window_text = get_window(20503)
print(f"--- WINDOW START (first 500 chars) ---")
print(window_text[:500])
print(f"-------------------------------------")

user_msg = f"=== ФРАГМЕНТ ТРАНСКРИПТА КОФЕЙНИ ===\n{window_text}\n\n"
user_msg += "Найди ПЕРВЫЙ диалог заказа в этом фрагменте транскрипта, который начинается строго ПОСЛЕ 20503 секунды."
# We also provide prev_dialog_tail
prev_dialog_tail = """[20485 - 20486] БАРИСТА: Да, конечно.
[20487 - 20490] БАРИСТА: Так, тут белый
[20493 - 20495] БАРИСТА: 680.
[20500 - 20503] БАРИСТА: Хорошо, первый номер"""
user_msg += f"\n\nПоследние строки ПРЕДЫДУЩЕГО диалога (проверь, не был ли он обрезан):\n{prev_dialog_tail}"
user_msg += "\n\nВыдай только текст диалога строго по формату."

payload = {
    "model": "deepseek-v4-flash",
    "messages": [
        {"role": "system", "content": sys_content},
        {"role": "user", "content": user_msg}
    ],
    "max_tokens": 16000,
    "temperature": 0.1,
    "extra_body": {
        "thinking": {
            "type": "enabled",
            "budget_tokens": 8000
        }
    }
}

print("Calling DeepSeek API...")
resp = requests.post(URL, headers=headers, json=payload, timeout=300)
if resp.status_code == 200:
    res = resp.json()
    choice = res['choices'][0]['message']
    
    # Check thinking
    thinking = choice.get('reasoning_content') or choice.get('thinking') or ""
    if not thinking and 'reasoning' in choice:
        thinking = choice['reasoning']
    
    print("\n=== THINKING PATH ===")
    print(thinking)
    print("\n=== RESPONSE CONTENT ===")
    print(choice.get('content'))
    
    usage = res.get('usage', {})
    print(f"\nTokens: {usage}")
else:
    print(f"API Error {resp.status_code}: {resp.text}")
