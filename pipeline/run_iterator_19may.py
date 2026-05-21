"""
run_iterator_19may.py — v3 (Window Pipeline)
Вместо полного транскрипта в system prompt, каждый запрос получает
динамическое окно ~10000 символов начиная с конца предыдущего диалога.
Это дешевле, быстрее и надёжнее (модель не может перескочить диалог).
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
WINDOW_SIZE = 10000  # символов (~12-15 минут транскрипта)
WINDOW_EXPAND = 5000  # расширение если диалог не влез

# ===================== ЗАГРУЗКА =====================
def load_prompt(fname):
    p = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'docs', fname)
    with open(p, 'r', encoding='utf-8') as f:
        return f.read()

iterator_prompt = load_prompt('iterator_prompt.md')
qa_prompt = load_prompt('qa_prompt.md')

# Загружаем canvas как массив строк с разобранными таймкодами
print(f"[*] Загружаем canvas: {CANVAS_FILE}")
with open(CANVAS_FILE, 'r', encoding='utf-8') as f:
    canvas_lines = f.readlines()

# Парсим таймкоды для каждой строки
parsed_canvas = []
for line in canvas_lines:
    match = re.match(r'\[(\d+)\s*-\s*(\d+)\]', line.strip())
    if match:
        parsed_canvas.append({
            "start": int(match.group(1)),
            "end": int(match.group(2)),
            "text": line.strip()
        })

print(f"[*] Загружено {len(parsed_canvas)} строк транскрипта")
if parsed_canvas:
    total_seconds = parsed_canvas[-1]["end"] - parsed_canvas[0]["start"]
    print(f"[*] Диапазон: {parsed_canvas[0]['start']} - {parsed_canvas[-1]['end']} сек (~{total_seconds//3600}ч {(total_seconds%3600)//60}мин)")

# System prompt = ТОЛЬКО правила (без транскрипта!)
sys_content = iterator_prompt

def get_window(after_second, size=WINDOW_SIZE):
    """Вырезает окно из canvas начиная с after_second.
    Возвращает текст окна и флаг is_end (больше нет строк)."""
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
    
    if not window_lines:
        return None, True  # Конец транскрипта
    
    return "\n".join(window_lines), False

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
all_results = []

def qa_worker():
    """Поток 2: берёт диалоги из очереди, оценивает через Chat V3, пушит в Supabase."""
    while True:
        item = qa_queue.get()
        if item is None:
            break
        
        idx = item["idx"]
        text = item["text"]
        
        print(f"\n[QA] Оцениваем диалог #{idx}...")
        evaluated = run_qa_single(text, idx)
        
        if evaluated:
            print(f"[QA] Диалог #{idx} оценён!")
            
            print(f"[SUPABASE] Отправляем диалог #{idx}...")
            ok = push_single_dialog(evaluated, idx, DATE_FOLDER)
            if ok:
                print(f"[SUPABASE] Диалог #{idx} → дашборд ✅")
            
            all_results.append({"idx": idx, "evaluation": evaluated})
        else:
            print(f"[QA] Диалог #{idx} — ошибка оценки")
        
        qa_queue.task_done()

qa_thread = threading.Thread(target=qa_worker, daemon=True)
qa_thread.start()

# ===================== ИТЕРАТОР (Reasoner) — Поток 1 =====================
last_second = 0
dialog_idx = 1
prev_dialog_tail = ""
all_dialogues_raw = []
consecutive_empty = 0  # Счётчик пустых ответов подряд

print(f"\n[ITERATOR] Старт разбора дня {DATE_FOLDER} (лимит: {MAX_DIALOGUES} диалогов)...")
print(f"[ITERATOR] Режим: ДИНАМИЧЕСКОЕ ОКНО ({WINDOW_SIZE} символов)\n")

while dialog_idx <= MAX_DIALOGUES:
    # Вырезаем окно из canvas
    window_text, is_end = get_window(last_second, WINDOW_SIZE)
    
    if is_end or window_text is None:
        print("[ITERATOR] Достигнут конец транскрипта.")
        break
    
    window_chars = len(window_text)
    window_lines_count = window_text.count('\n') + 1
    print(f" -> [{datetime.datetime.now().strftime('%H:%M:%S')}] Запрос #{dialog_idx} | окно: {last_second}с+ | {window_chars} симв, {window_lines_count} строк")
    
    # Формируем запрос
    if last_second == 0:
        user_msg = f"Вот фрагмент транскрипта кофейни. Найди ПЕРВЫЙ диалог заказа в этом фрагменте. Выдай только его текст строго по формату.\n\n=== ФРАГМЕНТ ТРАНСКРИПТА ===\n{window_text}"
    else:
        user_msg = f"Вот фрагмент транскрипта кофейни (начинается после {last_second} секунды). Найди ПЕРВЫЙ диалог заказа в этом фрагменте."
        if prev_dialog_tail:
            user_msg += f"\n\nПоследние строки ПРЕДЫДУЩЕГО диалога (проверь, не был ли он обрезан):\n{prev_dialog_tail}"
        user_msg += f"\n\nВыдай только текст диалога строго по формату.\n\n=== ФРАГМЕНТ ТРАНСКРИПТА ===\n{window_text}"

    payload = {
        "model": "deepseek-reasoner",
        "messages": [
            {"role": "system", "content": sys_content},
            {"role": "user", "content": user_msg}
        ],
        "max_tokens": 8000
    }

    try:
        resp = requests.post(URL, headers=headers, json=payload, timeout=300)
        if resp.status_code == 200:
            result = resp.json()
            choice = result['choices'][0]['message']
            answer = (choice.get('content') or '').strip()
            
            # Логируем использование токенов
            usage = result.get('usage', {})
            prompt_tokens = usage.get('prompt_tokens', 0)
            cached_tokens = usage.get('prompt_cache_hit_tokens', 0)
            completion_tokens = usage.get('completion_tokens', 0)
            print(f"    [TOKENS] prompt={prompt_tokens} (cached={cached_tokens}) completion={completion_tokens}")

            if not answer or answer.strip() == "END" or answer.strip().endswith("END"):
                print("[ITERATOR] Получен END. Разбор завершён.")
                break

            # Извлекаем таймкоды
            times = re.findall(r'\[(\d+)\s*-\s*(\d+)\]', answer)
            if not times:
                print(f"[!] Нет таймкодов в ответе. Пробуем сдвиг +300 сек.")
                print(f"    Ответ: {answer[:200]}")
                last_second += 300
                consecutive_empty += 1
                if consecutive_empty >= 3:
                    print("[ITERATOR] 3 пустых ответа подряд — завершаем.")
                    break
                continue

            consecutive_empty = 0
            start_times = [int(t[0]) for t in times]
            end_times = [int(t[1]) for t in times]
            min_time = min(start_times)
            max_time = max(end_times)

            if max_time <= last_second:
                print(f"[!] Время {max_time} <= {last_second}. Сдвигаем +60 сек.")
                last_second += 60
                continue

            # Проверка: есть ли оплата/прощание/номерок в ответе (диалог не обрезан?)
            has_ending = any(kw in answer.lower() for kw in [
                'к оплате', 'картой', 'наличкой', 'наличными', 'прикладывайте', 
                'приложите', 'номерочек', 'номерок', 'хорошего', 'до свидания',
                'всего доброго', 'пожалуйста', 'сдача', 'спасибо', 'приятного'
            ])
            
            if not has_ending and window_chars < WINDOW_SIZE + WINDOW_EXPAND * 2:
                # Диалог может быть обрезан окном — расширяем
                expanded_window, _ = get_window(last_second, WINDOW_SIZE + WINDOW_EXPAND)
                if expanded_window and len(expanded_window) > window_chars:
                    print(f"    [!] Диалог может быть обрезан. Расширяю окно до {len(expanded_window)} симв...")
                    # Повторяем запрос с расширенным окном
                    user_msg_expanded = user_msg.replace(window_text, expanded_window)
                    payload["messages"][1]["content"] = user_msg_expanded
                    resp2 = requests.post(URL, headers=headers, json=payload, timeout=300)
                    if resp2.status_code == 200:
                        answer2 = (resp2.json()['choices'][0]['message'].get('content') or '').strip()
                        times2 = re.findall(r'\[(\d+)\s*-\s*(\d+)\]', answer2)
                        if times2:
                            answer = answer2
                            start_times = [int(t[0]) for t in times2]
                            end_times = [int(t[1]) for t in times2]
                            min_time = min(start_times)
                            max_time = max(end_times)
                            print(f"    [OK] Расширенный диалог: {min_time}-{max_time}")

            last_second = max_time

            # GigaAM-Emo
            h = min_time // 3600
            m = (min_time % 3600) // 60
            print(f"[ITERATOR] Диалог #{dialog_idx} найден ({h}:{m:02d}, {min_time}-{max_time} сек). Эмоции...")
            emo_tag, is_conflict = get_emotion_tag(min_time, max_time)
            print(f"[EMO] {emo_tag}")

            final_text = f"{emo_tag}\n{answer}"
            
            all_dialogues_raw.append({
                "idx": dialog_idx,
                "min_time": min_time,
                "max_time": max_time,
                "text": final_text,
                "is_conflict_emo": is_conflict
            })

            # Отправляем в QA-очередь
            qa_queue.put({"idx": dialog_idx, "text": final_text})

            # Сохраняем хвост
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

qa_queue.join()
qa_queue.put(None)
qa_thread.join()

# ===================== БЭКАП НА ДИСК =====================
with open(RESULTS_FILE.replace('.json', '_raw.json'), 'w', encoding='utf-8') as f:
    json.dump(all_dialogues_raw, f, ensure_ascii=False, indent=2)

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
