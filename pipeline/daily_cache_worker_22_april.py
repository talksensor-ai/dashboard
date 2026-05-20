import os
import sys
import time
import json
import requests
import re
import datetime
from dotenv import load_dotenv
import yadisk
from audio_audit_pipeline import run_gigaam
from push_to_supabase import push_report_to_supabase

env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(env_path)

API_KEY = os.environ.get("DEEPSEEK_API_KEY")
URL = "https://api.deepseek.com/chat/completions"

def timestamp_to_seconds(ts_str):
    """Converts 'HH-MM-SS' or 'HH-MM-DD-MM-YYYY' to absolute seconds from midnight."""
    parts = ts_str.split('-')
    h = int(parts[0])
    m = int(parts[1])
    s = int(parts[2]) if len(parts) == 3 else 0
    return h * 3600 + m * 60 + s

def shift_timestamps_in_text(raw_text, shift_sec):
    """Adds shift_sec to all [start - end] timestamps in GigaAM output."""
    lines = raw_text.split('\n')
    new_lines = []
    # Pattern to match [XX - YY]
    pattern = re.compile(r'^\[(\d+)\s*-\s*(\d+)\](.*)$')
    for line in lines:
        match = pattern.match(line.strip())
        if match:
            start_s = int(match.group(1)) + shift_sec
            end_s = int(match.group(2)) + shift_sec
            text = match.group(3)
            new_lines.append(f"[{start_s} - {end_s}]{text}")
        else:
            if line.strip():
                new_lines.append(line)
    return "\n".join(new_lines)

def run_qa_on_dialog(clean_dialog_text, dialog_index, date_folder, shop_id):
    """Sends isolated clean dialog to Chat V3 for QA JSON generation."""
    qa_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'docs', 'qa_prompt.md')
    with open(qa_path, 'r', encoding='utf-8') as f:
        qa_instruction = f.read()

    glossary_path = os.path.join(os.path.dirname(__file__), 'glossary.json')
    if os.path.exists(glossary_path):
        with open(glossary_path, 'r', encoding='utf-8') as f:
            qa_instruction += "\n\nГЛОССАРИЙ:\n" + f.read()

    headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {API_KEY}'}
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": qa_instruction},
            {"role": "user", "content": clean_dialog_text}
        ],
        "max_tokens": 4000,
        "response_format": {"type": "json_object"} # Important for JSON out
    }
    
    print(f"[QA] Оцениваем диалог #{dialog_index}...")
    try:
        resp = requests.post(URL, headers=headers, json=payload, timeout=60)
        if resp.status_code == 200:
            json_content = resp.json()['choices'][0]['message']['content']
            match = re.search(r'```json\s*(.*?)\s*```', json_content, re.DOTALL)
            json_str = match.group(1) if match else json_content.strip()
            
            try:
                parsed = json.loads(json_str)
                # Ensure structure
                if "dialogues" not in parsed:
                    parsed = {"dialogues": [parsed]}
                
                # Write individual report
                tmp_json = f"FINAL_AUDIT_REPORT_{dialog_index}.json"
                with open(tmp_json, "w", encoding="utf-8") as f:
                    json.dump(parsed, f, ensure_ascii=False, indent=2)
                
                # Push to supabase (no audio mapping for now, or we can map daily audio later)
                print(f"[QA] Пуш в БД диалога #{dialog_index}")
                push_report_to_supabase(tmp_json, shop_id=shop_id, audio_path="", date_folder=date_folder)
                
            except json.JSONDecodeError as err:
                print(f"[QA] Ошибка формата JSON: {err}")
        else:
            print(f"[QA] Ошибка API: {resp.status_code} - {resp.text}")
    except Exception as e:
        print(f"[QA] Исключение: {e}")

def run_cache_iterator(canvas_file, date_folder, shop_id):
    """Core logic to iterate over the entire day using DeepSeek Context Cache."""
    if not os.path.exists(canvas_file):
        print("Canvas file missing.")
        return

    with open(canvas_file, 'r', encoding='utf-8') as f:
        daily_transcript = f.read()
        
    iterator_p = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'docs', 'iterator_prompt.md')
    with open(iterator_p, 'r', encoding='utf-8') as f:
        base_prompt = f.read()
        
    sys_content = base_prompt + "\n\n=== ТРАНСКРИПТ КОФЕЙНИ ===\n\n" + daily_transcript
    
    headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {API_KEY}'}
    
    last_second = 0
    dialog_idx = 1
    
    print("\n[ITERATOR] Запуск разбора дня...")
    
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
            "max_tokens": 4000
        }
        
        print(f" -> Запрос диалога после {last_second} сек...")
        try:
            resp = requests.post(URL, headers=headers, json=payload, timeout=240)
            if resp.status_code == 200:
                answer = resp.json()['choices'][0]['message']['content'].strip()
                
                if answer.strip() == "END" or "END" in answer[-10:]:
                    print("[ITERATOR] Получен END. Разбор дня завершен.")
                    break
                    
                # Extract max timestamp to move pointer Forward
                times = re.findall(r'\[(\d+)\s*-\s*(\d+)\]', answer)
                if times:
                    end_times = [int(t[1]) for t in times]
                    max_time = max(end_times)
                    
                    if max_time <= last_second:
                        print(f"[!] Внимание: извлеченное время {max_time} меньше или равно {last_second}. Чтобы избежать бесконечного цикла, прибавим 10 сек.")
                        last_second += 10
                    else:
                        last_second = max_time
                else:
                    print("[!] Модель не вернула таймкоды. Завершаем цикл (или сбой).")
                    print(f"Ответ: {answer}")
                    break
                    
                # Run QA locally
                print(f"[ITERATOR] Нашли диалог до {last_second} сек. Запускаем Аудит...")
                run_qa_on_dialog(answer, dialog_idx, date_folder, shop_id)
                dialog_idx += 1
                
            else:
                print(f"[ITERATOR] API ERROR {resp.status_code}: {resp.text}")
                break
        except Exception as e:
            print(f"[ITERATOR] Сбой соединения: {e}")
            break

def process_daily_folder(y, root_path, date_folder, shop_id):
    """Downloads all OGG files for a day, transcribes, merges with time-shifts, and invokes the iterator."""
    target_path = f"{root_path}/{date_folder}"
    print(f"\n====== ОБРАБОТКА ДНЯ: {date_folder} ======")
    try:
        items = list(y.listdir(target_path))
        oggs = [i.name for i in items if i.type == 'file' and i.name.endswith('.ogg')]
        oggs.sort()
    except Exception as e:
        print(f"Ошибка чтения директории {target_path} на Я.Диске: {e}")
        return

    canvas_file = f"daily_canvas_{date_folder}.txt"
    if os.path.exists(canvas_file):
         print(f"Склейка {canvas_file} уже существует, переходим к кэш-итератору.")
         run_cache_iterator(canvas_file, date_folder, shop_id)
         return
         
    combined_log = []
    
    for fname in oggs:
        local_ogg = f"{date_folder}_{fname}"
        local_txt = f"{date_folder}_{fname.replace('.ogg', '_transcript.txt')}"
        
        # Calculate Shift in Seconds: '14-30-00.ogg' -> 14*3600 + 30*60
        base = fname.replace('.ogg', '')
        try:
            shift_s = timestamp_to_seconds(base)
        except ValueError:
            print(f"Неизвестный формат времени {fname}. Принимаю время сдвига 0.")
            shift_s = 0
            
        try:
            # Download
            if not os.path.exists(local_ogg):
                 print(f"Скачивание {fname}...")
                 y.download(f"{target_path}/{fname}", local_ogg)
                 
            # Fix 0-byte file bug
            if os.path.exists(local_ogg) and os.path.getsize(local_ogg) < 1024:
                 print(f"[!] Файл {local_ogg} поврежден (весит слишком мало). Пропускаем.")
                 os.remove(local_ogg)
                 continue
                 
            # Transcribe
            if not os.path.exists(local_txt):
                 print(f"Транскрибация {fname}...")
                 run_gigaam(local_ogg, local_txt)
                 
            # Shift contents & append
            if os.path.exists(local_txt):
                 with open(local_txt, 'r', encoding='utf-8') as f:
                     raw_text = f.read()
                 shifted_text = shift_timestamps_in_text(raw_text, shift_s)
                 combined_log.append(f"\\n\\n=== ЧАНК: {fname} (Сдвиг: {shift_s} сек) ===\\n\\n")
                 combined_log.append(shifted_text)
                 
        except Exception as e:
            print(f"[ERROR] Критический сбой при обработке файла {fname}: {e}. Пропускаем файл и идем дальше.")
            continue
             
    with open(canvas_file, 'w', encoding='utf-8') as f:
         f.write("".join(combined_log))
         
    print(f"[+] Дневной транскрипт собран: {canvas_file}")
    
    # Run DeepSeek Iterator (DISABLED BY USER REQUEST)
    # run_cache_iterator(canvas_file, date_folder, shop_id)
    print("Canvas completely built! Stopping here per user request.")

if __name__ == "__main__":
    TOKEN = os.environ.get("YANDEX_TOKEN")
    if not TOKEN:
        print("YANDEX_TOKEN missing")
        exit(1)
        
    ya = yadisk.YaDisk(token=TOKEN)
    
    # Настройки
    CAFE_FOLDER = "/Ак мечеть"
    TARGET_DATE = "2026-04-13" # Заменить на любую дату (через sys.argv)
    if len(sys.argv) > 1:
        TARGET_DATE = sys.argv[1]
        
    SHOP_ID = 8 # Для Ак мечети, например
    
    process_daily_folder(ya, CAFE_FOLDER, TARGET_DATE, SHOP_ID)
