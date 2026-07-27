import os, sys, requests, json
# Set up sys.path
sys.path.append("/Users/ai/talk/pipeline")
from main import get_window, sys_content, URL, headers

window_text, is_end = get_window(20503)
print("Is end:", is_end)
print("Window text length:", len(window_text) if window_text else 0)
if window_text:
    print("First 200 chars of window:")
    print(window_text[:200])

user_msg = f"=== ФРАГМЕНТ ТРАНСКРИПТА КОФЕЙНИ ===\n{window_text}\n\n"
user_msg += "Найди ПЕРВЫЙ диалог заказа в этом фрагменте транскрипта, который начинается строго ПОСЛЕ 20503 секунды."
user_msg += "\n\nПоследние строки ПРЕДЫДУЩЕГО диалога (проверь, не был ли он обрезан):\n[20500 - 20503] БАРИСТА: Хорошо, первый номер"
user_msg += "\n\nВыдай только текст диалога строго по формату."

payload = {
    "model": "deepseek-v4-flash",
    "messages": [
        {"role": "system", "content": sys_content},
        {"role": "user", "content": user_msg}
    ],
    "max_tokens": 16000,
    "extra_body": {
        "thinking": {
            "type": "enabled",
            "budget_tokens": 8000
        }
    }
}

print("Sending request to deepseek-v4-flash...")
resp = requests.post(URL, headers=headers, json=payload, timeout=300)
print("Status:", resp.status_code)
if resp.status_code == 200:
    res = resp.json()
    choice = res['choices'][0]['message']
    print("--- CONTENT ---")
    print(choice.get('content'))
    print("--- THINKING ---")
    print(choice.get('reasoning_content'))
    print("--- USAGE ---")
    print(res.get('usage'))
else:
    print(resp.text)
