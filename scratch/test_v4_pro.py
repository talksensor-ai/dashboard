import os
import requests
import json
from dotenv import load_dotenv

load_dotenv('/Users/ai/talk/.env')

API_KEY = os.environ.get("DEEPSEEK_API_KEY")
URL = "https://api.deepseek.com/chat/completions"
headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {API_KEY}'}

sys_content = open('/Users/ai/talk/docs/iterator_prompt.md', 'r', encoding='utf-8').read()

# Let's get the window text after 3745
canvas_lines = open('/Users/ai/talk/daily_canvas_2026-05-21_cumulative.txt', 'r', encoding='utf-8').readlines()
window_lines = []
total_chars = 0
found_start = False
for line in canvas_lines:
    if '[3746' in line or found_start:
        found_start = True
        window_lines.append(line.strip())
        total_chars += len(line) + 1
        if total_chars >= 20000:
            break

window_text = "\n".join(window_lines)

user_msg = f"=== ФРАГМЕНТ ТРАНСКРИПТА КОФЕЙНИ ===\n{window_text}\n\n"
user_msg += "Найди ПЕРВЫЙ диалог заказа в этом фрагменте транскрипта, который начинается строго ПОСЛЕ 3745 секунды."
user_msg += "\n\nПоследние строки ПРЕДЫДУЩЕГО диалога (проверь, не был ли он обрезан):\n[3743 - 3745] КЛИЕНТ: Наверное, бонусное.\n[3744 -"
user_msg += "\n\nВыдай только текст диалога строго по формату."

payload = {
    "model": "deepseek-v4-pro",
    "messages": [
        {"role": "system", "content": sys_content},
        {"role": "user", "content": user_msg}
    ],
    "max_tokens": 4000,
    "extra_body": {
        "thinking": {
            "type": "disabled"
        }
    }
}

print("Sending request to deepseek-v4-pro...")
try:
    resp = requests.post(URL, headers=headers, json=payload, timeout=300)
    print("Status code:", resp.status_code)
    if resp.status_code == 200:
        result = resp.json()
        print("\n--- Usage ---")
        print(json.dumps(result.get('usage', {}), indent=2))
        
        choice = result['choices'][0]['message']
        content = choice.get('content', '')
        print("\n--- Content Length ---")
        print(len(content))
        
        print("\n--- First 500 chars of content ---")
        print(content[:500])
        print("\n--- Last 500 chars of content ---")
        print(content[-500:])
        
        # Check if reasoning_content is present
        reasoning = choice.get('reasoning_content')
        if reasoning:
            print("\n--- Reasoning Content Length ---")
            print(len(reasoning))
            print("\n--- First 300 chars of reasoning ---")
            print(reasoning[:300])
    else:
        print("Error:", resp.text)
except Exception as e:
    print("Failed request:", e)
