"""Итератор диалогов через DeepSeek Reasoner.
Берет холст за день и итеративно извлекает диалоги (заказы).
"""
import os
import sys
import requests
import time

sys.stdout.reconfigure(encoding='utf-8')
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

API_KEY = os.environ["DEEPSEEK_API_KEY"]
URL = "https://api.deepseek.com/chat/completions"
HEADERS = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

CANVAS_PATH = r"e:\talk\daily_canvas_2026-04-16.txt"
OUTPUT_DIR = r"e:\talk\dialogs_16"
ITERATOR_PROMPT_PATH = r"e:\talk\docs\iterator_prompt.md"

MAX_DIALOGS = 10

# Read iterator prompt
with open(ITERATOR_PROMPT_PATH, 'r', encoding='utf-8') as f:
    system_prompt = f.read()

# Read full canvas
with open(CANVAS_PATH, 'r', encoding='utf-8') as f:
    full_canvas = f.read()

# Canvas is huge (486KB). DeepSeek Reasoner has ~64K token limit.
# Russian text ~ 3 chars/token, so ~160K tokens — too much.
# Strategy: split canvas into overlapping windows of ~4000 lines,
# and advance the window as we find dialogues further in time.

canvas_lines = full_canvas.split('\n')
print(f"Холст: {len(canvas_lines)} строк, {len(full_canvas)} символов")

os.makedirs(OUTPUT_DIR, exist_ok=True)

def get_chunk(lines, start_line, max_lines=2500):
    """Get a chunk of the canvas starting from start_line."""
    end = min(start_line + max_lines, len(lines))
    return '\n'.join(lines[start_line:end]), end

def extract_last_timestamp(dialog_text):
    """Extract the last [XXXXX - YYYYY] timestamp from dialog text."""
    import re
    timestamps = re.findall(r'\[\d+\s*-\s*(\d+)\]', dialog_text)
    if timestamps:
        return int(timestamps[-1])
    return None

def find_line_by_timestamp(lines, timestamp):
    """Find the line index where a timestamp appears."""
    import re
    for i, line in enumerate(lines):
        match = re.search(r'\[(\d+)\s*-', line)
        if match and int(match.group(1)) >= timestamp:
            # Go back 5 lines for overlap
            return max(0, i - 5)
    return 0

dialog_count = 0
current_line = 0
last_timestamp = None

while dialog_count < MAX_DIALOGS:
    # Determine where to start reading
    if last_timestamp:
        current_line = find_line_by_timestamp(canvas_lines, last_timestamp)
    
    chunk, chunk_end = get_chunk(canvas_lines, current_line)
    
    if not chunk.strip():
        print("Холст закончился.")
        break
    
    # Build user message
    if dialog_count == 0:
        user_msg = f"Вот полотно транскрипта рабочего дня кофейни:\n\n{chunk}\n\nНайди первый диалог (заказ клиента)."
    else:
        user_msg = f"Вот полотно транскрипта рабочего дня кофейни:\n\n{chunk}\n\nНайди следующий диалог (заказ клиента) после таймкода [{last_timestamp}]."
    
    print(f"\n{'='*60}")
    print(f"Ищу диалог #{dialog_count + 1}... (строки {current_line}-{chunk_end}, ~{len(chunk)//1000}KB)")
    print(f"{'='*60}")
    
    payload = {
        "model": "deepseek-reasoner",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_msg}
        ]
    }
    
    try:
        t0 = time.time()
        resp = requests.post(URL, headers=HEADERS, json=payload, timeout=300)
        elapsed = time.time() - t0
        
        if resp.status_code != 200:
            print(f"Ошибка API: {resp.status_code} - {resp.text[:300]}")
            break
        
        data = resp.json()
        content = data['choices'][0]['message']['content'].strip()
        reasoning = data['choices'][0]['message'].get('reasoning_content', '')
        
        # Check usage
        usage = data.get('usage', {})
        print(f"Токены: input={usage.get('prompt_tokens',0)}, output={usage.get('completion_tokens',0)}, reasoning={usage.get('reasoning_tokens',0)}")
        print(f"Время: {elapsed:.1f} сек")
        
        # Check for END
        if content.strip().upper() == 'END':
            print("Резонер вернул END — больше диалогов нет.")
            break
        
        dialog_count += 1
        
        # Save dialog
        output_path = os.path.join(OUTPUT_DIR, f"dialog_{dialog_count:02d}.txt")
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"[OK] Dialog #{dialog_count} saved: {output_path}")
        print(f"Превью: {content[:200]}...")
        
        # Extract last timestamp for next iteration
        ts = extract_last_timestamp(content)
        if ts:
            last_timestamp = ts
            print(f"Последний таймкод: [{last_timestamp}]")
        else:
            print("[WARN] No timestamp found, advancing window by 500 lines")
            current_line = chunk_end - 200  # overlap
            last_timestamp = None
        
    except requests.exceptions.Timeout:
        print("Таймаут запроса (300 сек). Пробую снова...")
        continue
    except Exception as e:
        print(f"Ошибка: {e}")
        break

print(f"\n\n{'='*60}")
print(f"ИТОГО: Извлечено {dialog_count} диалогов из холста 16 апреля")
print(f"Файлы в: {OUTPUT_DIR}")
print(f"{'='*60}")
