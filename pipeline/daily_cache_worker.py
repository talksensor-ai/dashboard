import os
import sys
import time
import json
import queue
import threading
import requests
import re
import datetime
from dotenv import load_dotenv
import yadisk
from audio_audit_pipeline import run_gigaam
from push_to_supabase import push_report_to_supabase
from emotion_analyzer import analyze_emotion_and_tag

env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(env_path)

API_KEY = os.environ.get("DEEPSEEK_API_KEY")
URL = "https://api.deepseek.com/chat/completions"

def timestamp_to_seconds(ts_str):
    """Converts 'HH-MM-DD-MM-YYYY' to absolute seconds from midnight."""
    # Example: 09-00-25-04-2026.ogg
    parts = ts_str.split('-')
    if len(parts) < 2: return 0
    try:
        h = int(parts[0])
        m = int(parts[1])
        # In the format HH-MM-DD-MM-YYYY, there are no seconds.
        # parts[2] is the day, parts[3] is month, etc.
        return h * 3600 + m * 60
    except:
        return 0

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

# --------------- QA: BATCH BY 2 ---------------

def _load_qa_prompt():
    """Load QA system prompt + glossary (cached after first call)."""
    qa_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'docs', 'qa_prompt.md')
    with open(qa_path, 'r', encoding='utf-8') as f:
        qa_instruction = f.read()
    glossary_path = os.path.join(os.path.dirname(__file__), 'glossary.json')
    if os.path.exists(glossary_path):
        with open(glossary_path, 'r', encoding='utf-8') as f:
            qa_instruction += "\n\nГЛОССАРИЙ:\n" + f.read()
    return qa_instruction


def run_qa_on_batch(dialog_texts, start_index, date_folder, shop_id, audio_paths=None):
    """Sends a batch of 1-2 clean dialogues to Chat V3 for QA scoring.
    
    Args:
        dialog_texts: list of 1-2 dialogue text strings
        start_index: index of the first dialogue in the batch (for logging)
        date_folder: date string for Supabase
        shop_id: shop ID for Supabase
        audio_paths: list of paths to audio files (optional)
    """
    qa_instruction = _load_qa_prompt()
    
    # Combine dialogues with clear separators
    if len(dialog_texts) == 1:
        user_content = dialog_texts[0]
    else:
        parts = []
        for i, dt in enumerate(dialog_texts):
            parts.append(f"=== ДИАЛОГ #{start_index + i} ===\n{dt}")
        user_content = "\n\n".join(parts)
    
    headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {API_KEY}'}
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": qa_instruction},
            {"role": "user", "content": user_content}
        ],
        "max_tokens": 8000,
        "response_format": {"type": "json_object"}
    }
    
    batch_label = f"#{start_index}" if len(dialog_texts) == 1 else f"#{start_index}-{start_index + len(dialog_texts) - 1}"
    print(f"[QA] Оцениваем диалоги {batch_label} (батч {len(dialog_texts)})...")
    
    try:
        resp = requests.post(URL, headers=headers, json=payload, timeout=120)
        if resp.status_code == 200:
            json_content = resp.json()['choices'][0]['message']['content']
            match = re.search(r'```json\s*(.*?)\s*```', json_content, re.DOTALL)
            json_str = match.group(1) if match else json_content.strip()
            
            try:
                parsed = json.loads(json_str)
                if "dialogues" not in parsed:
                    parsed = {"dialogues": [parsed]}
                
                tmp_json = f"FINAL_AUDIT_REPORT_{start_index}.json"
                with open(tmp_json, "w", encoding="utf-8") as f:
                    json.dump(parsed, f, ensure_ascii=False, indent=2)
                
                print(f"[QA] Пуш в БД диалогов {batch_label}")
                # Use the first audio path from the batch (if batch size is 1, this is perfect)
                a_path = audio_paths[0] if audio_paths else ""
                push_report_to_supabase(tmp_json, shop_id=shop_id, audio_path=a_path, date_folder=date_folder)
                
                # Cleanup temp audio files after push
                if audio_paths:
                    for ap in audio_paths:
                        if ap and os.path.exists(ap):
                            try:
                                os.remove(ap)
                            except:
                                pass
                
            except json.JSONDecodeError as err:
                print(f"[QA] Ошибка формата JSON: {err}")
        elif resp.status_code == 429:
            print(f"[QA] Rate limit. Ждем 10 сек...")
            time.sleep(10)
            run_qa_on_batch(dialog_texts, start_index, date_folder, shop_id)  # retry
        else:
            print(f"[QA] Ошибка API: {resp.status_code} - {resp.text[:300]}")
    except Exception as e:
        print(f"[QA] Исключение: {e}")

# Legacy wrapper for backward compatibility
def run_qa_on_dialog(clean_dialog_text, dialog_index, date_folder, shop_id):
    """Single-dialogue wrapper around run_qa_on_batch."""
    run_qa_on_batch([clean_dialog_text], dialog_index, date_folder, shop_id)


QA_BATCH_SIZE = 1  # Снизили до 1 для корректной привязки аудио к каждому диалогу

def run_cache_iterator(canvas_file, date_folder, shop_id, root_path="."):
    """Core logic to iterate over the entire day using DeepSeek Context Cache.
    
    Uses Reasoner for dialogue extraction (1 per call), GigaAM-Emo for acoustic 
    emotion evaluation, and Chat V3 for QA scoring (batched by QA_BATCH_SIZE for cost efficiency).
    """
    if not os.path.exists(canvas_file):
        print("Canvas file missing.")
        return

    with open(canvas_file, 'r', encoding='utf-8') as f:
        daily_transcript = f.read()
        
    iterator_p = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'docs', 'iterator_prompt.md')
    with open(iterator_p, 'r', encoding='utf-8') as f:
        base_prompt = f.read()
    
    glossary_path = os.path.join(os.path.dirname(__file__), 'glossary.json')
    if os.path.exists(glossary_path):
        with open(glossary_path, 'r', encoding='utf-8') as f:
            base_prompt += "\n\nГЛОССАРИЙ:\n" + f.read()
        
    sys_content = base_prompt + "\n\n=== ТРАНСКРИПТ КОФЕЙНИ ===\n\n" + daily_transcript
    
    headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {API_KEY}'}
    
    last_second = 0
    dialog_idx = 1
    qa_buffer = []  # Buffer for batch QA (texts)
    audio_buffer = [] # Buffer for batch QA (audio paths)
    
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
            "max_tokens": 8000
        }
        
        print(f" -> Запрос диалога после {last_second} сек...")
        try:
            resp = requests.post(URL, headers=headers, json=payload, timeout=300)
            if resp.status_code == 200:
                choice = resp.json()['choices'][0]['message']
                answer = (choice.get('content') or '').strip()
                
                if not answer or answer.strip() == "END" or "END" in answer[-10:]:
                    print("[ITERATOR] Получен END. Разбор дня завершен.")
                    break
                    
                # Extract max timestamp to move pointer forward
                times = re.findall(r'\[(\d+)\s*-\s*(\d+)\]', answer)
                if times:
                    start_times = [int(t[0]) for t in times]
                    end_times = [int(t[1]) for t in times]
                    min_time = min(start_times)
                    max_time = max(end_times)
                    
                    if max_time <= last_second:
                        print(f"[!] Время {max_time} <= {last_second}. Прибавляем 30 сек.")
                        last_second += 30
                    else:
                        last_second = max_time
                else:
                    print("[!] Модель не вернула таймкоды. Завершаем.")
                    print(f"Ответ: {answer[:300]}")
                    break
                    
                # Evaluate Emotion using GigaAM-Emo via acoustics
                print(f"[ITERATOR] Диалог #{dialog_idx} найден (с {min_time} по {max_time} сек). Оцениваем эмоции по звуку...")
                emo_tag, is_conflict, audio_path = analyze_emotion_and_tag(min_time, max_time, date_folder, root_path)
                
                # Append emo tag directly to dialogue text so Chat V3 sees it
                final_answer = f"{emo_tag}\n{answer}"
                
                # Buffer dialogue for batch QA
                qa_buffer.append((dialog_idx, final_answer))
                audio_buffer.append(audio_path)
                dialog_idx += 1
                
                # Flush QA buffer when it reaches batch size
                if len(qa_buffer) >= QA_BATCH_SIZE:
                    batch_texts = [t for _, t in qa_buffer]
                    batch_start = qa_buffer[0][0]
                    run_qa_on_batch(batch_texts, batch_start, date_folder, shop_id, audio_paths=audio_buffer)
                    qa_buffer.clear()
                    audio_buffer.clear()
                
                time.sleep(1)  # Помогает кешу прогреться
                
            elif resp.status_code == 429:
                print("[ITERATOR] Rate limit. Ждем 10 сек...")
                time.sleep(10)
                continue
            else:
                print(f"[ITERATOR] API ERROR {resp.status_code}: {resp.text[:300]}")
                break
        except Exception as e:
            print(f"[ITERATOR] Сбой соединения: {e}")
            break
    
    # Flush remaining buffered dialogues
    if qa_buffer:
        batch_texts = [t for _, t in qa_buffer]
        batch_start = qa_buffer[0][0]
        run_qa_on_batch(batch_texts, batch_start, date_folder, shop_id, audio_paths=audio_buffer)
        qa_buffer.clear()
        audio_buffer.clear()

def process_daily_folder(y, root_path, date_folder, shop_id):
    """Downloads all OGG files for a day, transcribes, merges with time-shifts, and invokes the iterator.
    
    Optimization: uses a background download thread so the next file is fetched
    while the GPU is busy transcribing the current one.
    """
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
          print(f"Склейка {canvas_file} уже существует. DeepSeek итератор отключен по запросу пользователя.")
          # run_cache_iterator(canvas_file, date_folder, shop_id, root_path="/Users/ai/talk")
          return
         
    combined_log = []

    # --- Параллельная загрузка: качаем N+1 пока транскрибируем N ---
    download_q = queue.Queue(maxsize=2)  # буфер до 2 файлов

    def _downloader():
        """Фоновый поток: скачивает файлы в очередь."""
        for fname in oggs:
            local_ogg = f"{date_folder}_{fname}"
            try:
                if not os.path.exists(local_ogg):
                    print(f"[↓] Скачиваем {fname}...")
                    y.download(f"{target_path}/{fname}", local_ogg)
                    # Проверяем размер
                    if os.path.exists(local_ogg) and os.path.getsize(local_ogg) < 1024:
                        print(f"[!] Файл {local_ogg} поврежден. Пропускаем.")
                        os.remove(local_ogg)
                        download_q.put(None)  # сигнал пропуска
                        continue
                else:
                    print(f"[↓] {fname} уже скачан.")
                download_q.put(fname)
            except Exception as e:
                print(f"[ERROR] Сбой при скачивании {fname}: {e}")
                download_q.put(None)  # сигнал ошибки
        download_q.put("__DONE__")  # sentinel

    downloader_thread = threading.Thread(target=_downloader, daemon=True)
    downloader_thread.start()

    while True:
        item = download_q.get()
        if item == "__DONE__":
            break
        if item is None:
            continue  # пропускаем сломанный файл

        fname = item
        local_ogg = f"{date_folder}_{fname}"
        local_txt = f"{date_folder}_{fname.replace('.ogg', '_transcript.txt')}"

        base = fname.replace('.ogg', '')
        try:
            shift_s = timestamp_to_seconds(base)
        except ValueError:
            print(f"Неизвестный формат времени {fname}. Принимаю сдвиг 0.")
            shift_s = 0

        try:
            # Транскрибируем (модель уже загружена в памяти, повторная загрузка не происходит)
            if not os.path.exists(local_txt):
                print(f"[≈] Транскрибируем {fname}...")
                run_gigaam(local_ogg, local_txt)

            # Сдвиг временных меток и добавление в общий лог
            if os.path.exists(local_txt):
                with open(local_txt, 'r', encoding='utf-8') as f:
                    raw_text = f.read()
                shifted_text = shift_timestamps_in_text(raw_text, shift_s)
                combined_log.append(f"\n\n=== ЧАНК: {fname} (Сдвиг: {shift_s} сек) ===\n\n")
                combined_log.append(shifted_text)

        except Exception as e:
            print(f"[ERROR] Критический сбой при обработке {fname}: {e}. Пропускаем.")
            continue

    downloader_thread.join()

    with open(canvas_file, 'w', encoding='utf-8') as f:
         f.write("".join(combined_log))
         
    print(f"[+] Дневной транскрипт собран: {canvas_file}")
    
    # Run DeepSeek Iterator 
    # run_cache_iterator(canvas_file, date_folder, shop_id, root_path="/Users/ai/talk")
    print("[!] DeepSeek итератор отключен по запросу пользователя (экономия баланса).")
    print("Pipeline successfully completed for the day!")


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
