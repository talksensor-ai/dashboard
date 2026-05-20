import os
import time
import requests
import re
from dotenv import load_dotenv

load_dotenv('e:/talk/.env')
API_KEY = os.environ.get("DEEPSEEK_API_KEY")

with open('e:/talk/docs/iterator_prompt.md', 'r', encoding='utf-8') as f:
    base_prompt = f.read()

with open('e:/talk/pipeline/glossary.json', 'r', encoding='utf-8') as f:
    glossary = f.read()

with open('e:/talk/transcript_13_00_blind.txt', 'r', encoding='utf-8') as f:
    transcript = f.read()

sys_content = base_prompt + "\n\nГЛОССАРИЙ:\n" + glossary + "\n\n=== ТРАНСКРИПТ КОФЕЙНИ ===\n\n" + transcript
headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {API_KEY}'}

last_second = 0
dialog_idx = 1
all_dialogues = []

print("Starting iterator over 1-hour transcript...")

while True:
    if last_second == 0:
        prompt = "Найди первый диалог заказа (или конфликт/дозаказ). Выдай только его отредактированный чистый текст с таймкодами."
    else:
        prompt = f"Найди следующий диалог заказа, который начался СТРОГО ПОСЛЕ {last_second} секунды. Выдай только его текст."
        
    payload = {
        "model": "deepseek-reasoner",
        "messages": [
            {"role": "system", "content": sys_content},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 8000
    }
    
    print(f" -> Querying dialogue after {last_second} sec...", flush=True)
    try:
        resp = requests.post("https://api.deepseek.com/chat/completions", headers=headers, json=payload, timeout=300)
        if resp.status_code == 200:
            choice = resp.json()['choices'][0]['message']
            answer = (choice.get('content') or '').strip()
            
            if not answer or answer.strip() == "END" or "END" in answer[-10:]:
                print("Got END. Finished.", flush=True)
                break
                
            times = re.findall(r'\[(\d+)\s*-\s*(\d+)\]', answer)
            if times:
                end_times = [int(t[1]) for t in times]
                max_time = max(end_times)
                
                if max_time <= last_second:
                    last_second += 30
                else:
                    last_second = max_time
            else:
                break
                
            print(f"   Found Dialogue #{dialog_idx} (up to {last_second} sec)", flush=True)
            all_dialogues.append(f"### Диалог #{dialog_idx}\n{answer}\n")
            dialog_idx += 1
            
            # To avoid rate limits
            time.sleep(1)
        elif resp.status_code == 429:
            print("Rate limit. Sleeping 10s...", flush=True)
            time.sleep(10)
            continue
        else:
            print(f"API ERROR {resp.status_code}", flush=True)
            break
    except Exception as e:
        print(f"Exception: {e}", flush=True)
        break

with open("e:/talk/full_hour_dialogues.md", "w", encoding="utf-8") as f:
    f.write("\n".join(all_dialogues))

print(f"Done! Saved {len(all_dialogues)} dialogues to full_hour_dialogues.md", flush=True)
