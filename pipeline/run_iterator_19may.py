"""
run_iterator_19may.py — v2 (Streaming Pipeline)
Каждый диалог сразу проходит весь путь: Reasoner → Emo → Chat V3 → Supabase
Два потока: Reasoner ищет следующий диалог, пока QA оценивает предыдущий.
"""
import os
import sys
import json
import time
import re
import requests
import datetime
import threading
import queue
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(env_path)

os.environ["PATH"] = os.environ.get("PATH", "") + ":/opt/homebrew/bin"
os.environ["PYTORCH_MPS_HIGH_WATERMARK_RATIO"] = "0.0"

import warnings
warnings.filterwarnings("ignore")

API_KEY = os.environ.get("DEEPSEEK_API_KEY")
URL = "https://api.deepseek.com/chat/completions"
headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {API_KEY}'}

DATE_FOLDER = "2026-05-19"
SHOP_ID = 8
SHOP_NAME = "Ак мечеть"
CANVAS_FILE = "/Users/ai/talk/pipeline/daily_canvas_2026-05-19.txt"
RESULTS_FILE = "/Users/ai/talk/pipeline/results_2026-05-19.json"
OGG_DIR = "/Users/ai/talk/pipeline"

MAX_DIALOGUES = 5  # Лимит на тестовый запуск

# ===================== ЗАГРУЗКА =====================
def load_prompt(fname):
    p = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'docs', fname)
    with open(p, 'r', encoding='utf-8') as f:
        return f.read()

iterator_prompt = load_prompt('iterator_prompt.md')
qa_prompt = load_prompt('qa_prompt.md')

print(f"[*] Загружаем canvas: {CANVAS_FILE}")
with open(CANVAS_FILE, 'r', encoding='utf-8') as f:
    daily_transcript = f.read()
print(f"[*] Размер транскрипта: {len(daily_transcript)} символов")

sys_content = iterator_prompt + "\n\n=== ТРАНСКРИПТ КОФЕЙНИ ===\n\n" + daily_transcript

# ===================== ЭМОЦИИ =====================
def get_emotion_tag(min_time, max_time):
    try:
        import torch
        if torch.backends.mps.is_available():
            torch.mps.empty_cache()
        from emotion_analyzer import analyze_emotion_and_tag
        tag, is_conflict, _ = analyze_emotion_and_tag(min_time, max_time, DATE_FOLDER, OGG_DIR)
        if torch.backends.mps.is_available():
            torch.mps.empty_cache()
        return tag, is_conflict
    except Exception as e:
        print(f"[EMO] Ошибка: {e}")
        return "[ЭМОЦИИ: ОШИБКА]", False

# ===================== QA (Chat V3) =====================
def run_qa_single(dialog_text, dialog_idx):
    """Оценивает один диалог через Chat V3, возвращает JSON."""
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": qa_prompt},
            {"role": "user", "content": f"Оцени следующий диалог и верни JSON:\n\n--- ДИАЛОГ #{dialog_idx} ---\n{dialog_text}\n"}
        ],
        "max_tokens": 4000,
        "response_format": {"type": "json_object"}
    }
    try:
        resp = requests.post(URL, headers=headers, json=payload, timeout=300)
        if resp.status_code == 200:
            content = resp.json()['choices'][0]['message']['content']
            data = json.loads(content)
            dialogues = data.get('dialogues', [])
            return dialogues[0] if dialogues else data
        elif resp.status_code == 429:
            print(f"[QA] Rate limit, ждём 15 сек...")
            time.sleep(15)
            return run_qa_single(dialog_text, dialog_idx)
        else:
            print(f"[QA] API ERROR {resp.status_code}: {resp.text[:200]}")
            return None
    except Exception as e:
        print(f"[QA] Ошибка: {e}")
        return None

# ===================== PUSH TO SUPABASE =====================
def push_single_dialog(evaluated, dialog_idx, date_folder):
    """Пушит один оценённый диалог в Supabase."""
    try:
        from push_to_supabase import push_report_to_supabase
        
        # Формируем мини-отчёт с одним диалогом
        report = {"dialogues": [evaluated]}
        tmp_path = f"/tmp/dialog_{dialog_idx}.json"
        with open(tmp_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False)
        
        push_report_to_supabase(
            json_path=tmp_path,
            shop_id=SHOP_ID,
            audio_path="",
            date_folder=date_folder,
            shop_name=SHOP_NAME
        )
        os.remove(tmp_path)
        return True
    except Exception as e:
        print(f"[SUPABASE] Ошибка: {e}")
        return False

# ===================== ОЧЕРЕДЬ QA =====================
qa_queue = queue.Queue()
all_results = []  # Бэкап всех результатов

def qa_worker():
    """Поток 2: берёт диалоги из очереди, оценивает через Chat V3, пушит в Supabase."""
    while True:
        item = qa_queue.get()
        if item is None:  # Сигнал завершения
            break
        
        idx = item["idx"]
        text = item["text"]
        
        print(f"\n[QA] Оцениваем диалог #{idx}...")
        evaluated = run_qa_single(text, idx)
        
        if evaluated:
            print(f"[QA] Диалог #{idx} оценён!")
            
            # Пушим в Supabase сразу
            print(f"[SUPABASE] Отправляем диалог #{idx}...")
            ok = push_single_dialog(evaluated, idx, DATE_FOLDER)
            if ok:
                print(f"[SUPABASE] Диалог #{idx} → дашборд ✅")
            
            # Бэкап
            all_results.append({"idx": idx, "evaluation": evaluated})
        else:
            print(f"[QA] Диалог #{idx} — ошибка оценки")
        
        qa_queue.task_done()

# Запускаем QA-воркер в отдельном потоке
qa_thread = threading.Thread(target=qa_worker, daemon=True)
qa_thread.start()

# ===================== ИТЕРАТОР (Reasoner) — Поток 1 =====================
last_second = 0
dialog_idx = 1
prev_dialog_tail = ""
all_dialogues_raw = []

print(f"\n[ITERATOR] Старт разбора дня {DATE_FOLDER} (лимит: {MAX_DIALOGUES} диалогов)...\n")

while dialog_idx <= MAX_DIALOGUES:
    if last_second == 0:
        prompt = "Найди первый диалог заказа (или конфликт/дозаказ). Выдай только его текст строго по формату."
    else:
        prompt = f"Найди следующий диалог заказа, который начался СТРОГО ПОСЛЕ {last_second} секунды."
        if prev_dialog_tail:
            prompt += f"\n\nПоследние строки ПРЕДЫДУЩЕГО диалога (проверь, не был ли он обрезан):\n{prev_dialog_tail}"
        prompt += "\n\nВыдай только текст диалога строго по формату."

    payload = {
        "model": "deepseek-reasoner",
        "messages": [
            {"role": "system", "content": sys_content},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 8000
    }

    print(f" -> [{datetime.datetime.now().strftime('%H:%M:%S')}] Запрос диалога #{dialog_idx} после {last_second} сек...")
    try:
        resp = requests.post(URL, headers=headers, json=payload, timeout=300)
        if resp.status_code == 200:
            choice = resp.json()['choices'][0]['message']
            answer = (choice.get('content') or '').strip()

            if not answer or answer.strip() == "END" or answer.strip().endswith("END"):
                print("[ITERATOR] Получен END. Разбор завершён.")
                break

            # Извлекаем таймкоды
            times = re.findall(r'\[(\d+)\s*-\s*(\d+)\]', answer)
            if not times:
                print(f"[!] Нет таймкодов в ответе. Завершаем.\nОтвет: {answer[:200]}")
                break

            start_times = [int(t[0]) for t in times]
            end_times = [int(t[1]) for t in times]
            min_time = min(start_times)
            max_time = max(end_times)

            if max_time <= last_second:
                print(f"[!] Время {max_time} <= {last_second}. Прибавляем 60 сек.")
                last_second += 60
                continue

            last_second = max_time

            # GigaAM-Emo
            h = min_time // 3600
            m = (min_time % 3600) // 60
            print(f"[ITERATOR] Диалог #{dialog_idx} найден ({h}:{m:02d}, {min_time}-{max_time} сек). Эмоции...")
            emo_tag, is_conflict = get_emotion_tag(min_time, max_time)
            print(f"[EMO] {emo_tag}")

            final_text = f"{emo_tag}\n{answer}"
            
            # Сохраняем сырой диалог
            all_dialogues_raw.append({
                "idx": dialog_idx,
                "min_time": min_time,
                "max_time": max_time,
                "text": final_text,
                "is_conflict_emo": is_conflict
            })

            # Отправляем в QA-очередь (поток 2 подхватит)
            qa_queue.put({"idx": dialog_idx, "text": final_text})

            # Сохраняем хвост для проверки обрезки
            answer_lines = [l for l in answer.strip().split('\n') if l.strip()]
            prev_dialog_tail = '\n'.join(answer_lines[-3:]) if answer_lines else ""

            dialog_idx += 1
            time.sleep(2)

        elif resp.status_code == 429:
            print("[ITERATOR] Rate limit. Ждём 15 сек...")
            time.sleep(15)
            continue
        else:
            print(f"[ITERATOR] API ERROR {resp.status_code}: {resp.text[:300]}")
            break

    except Exception as e:
        print(f"[ITERATOR] Сбой: {e}")
        break

# ===================== ЖДЁМ ЗАВЕРШЕНИЯ QA =====================
print(f"\n[*] Reasoner закончил. Найдено диалогов: {len(all_dialogues_raw)}")
print("[*] Ждём завершения QA-оценки оставшихся диалогов...")

qa_queue.join()  # Ждём пока все диалоги в очереди будут обработаны
qa_queue.put(None)  # Сигнал завершения QA-воркеру
qa_thread.join()

# ===================== БЭКАП НА ДИСК =====================
# Сохраняем сырые диалоги
with open(RESULTS_FILE.replace('.json', '_raw.json'), 'w', encoding='utf-8') as f:
    json.dump(all_dialogues_raw, f, ensure_ascii=False, indent=2)

# Сохраняем оценённые
final_result = {
    "date": DATE_FOLDER,
    "shop_id": SHOP_ID,
    "shop_name": SHOP_NAME,
    "processed_at": datetime.datetime.now().isoformat(),
    "total_dialogues": len(all_results),
    "results": all_results
}
with open(RESULTS_FILE, 'w', encoding='utf-8') as f:
    json.dump(final_result, f, ensure_ascii=False, indent=2)

print(f"\n[*] Бэкап сохранён: {RESULTS_FILE}")
print(f"[*] Итого обработано: {len(all_results)} диалогов")
print("\n=== PIPELINE COMPLETE ===")
