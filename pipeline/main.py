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

import argparse

# Parse arguments FIRST so we can use DATE_FOLDER
parser = argparse.ArgumentParser(description='Audio Audit Pipeline')
parser.add_argument('--skip-time', type=int, default=0, help='Seconds to skip from start')
parser.add_argument('--date', nargs='?', default='2026-05-21', help='Date in YYYY-MM-DD format (e.g., 2026-05-21)')
parser.add_argument('--limit', type=int, default=1, help='Max dialogues to process')
parser.add_argument('--start-idx', type=int, default=1, help='Starting dialogue index')
# parse_known_args in case other args are passed implicitly
args, _ = parser.parse_known_args()

DATE_FOLDER = args.date
SHOP_ID = 8
SHOP_NAME = "Ак-Мечеть"
CANVAS_FILE = f"/Users/ai/talk/daily_canvas_{DATE_FOLDER}_cumulative.txt"
RESULTS_FILE = f"/Users/ai/talk/pipeline/results_{DATE_FOLDER}.json"
OGG_DIR = "/Users/ai/talk"

MAX_DIALOGUES = args.limit
WINDOW_SIZE = 10000
WINDOW_EXPAND = 5000

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

# System prompt = ТОЛЬКО правила (без транскрипта!) + глоссарий
try:
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
    print("[*] Динамический глоссарий успешно загружен и добавлен в системный промпт.")
except Exception as ge:
    print(f"[*] Не удалось загрузить динамический глоссарий: {ge}")
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
        tag, is_conflict, audio_path = analyze_emotion_and_tag(min_time, max_time, "2026-05-21", OGG_DIR)
        if torch.backends.mps.is_available():
            torch.mps.empty_cache()
        return tag, is_conflict, audio_path
    except Exception as e:
        print(f"[EMO] Ошибка: {e}")
        return "[ЭМОЦИИ: ОШИБКА]", False, ""

# ===================== QA (Chat V3) =====================
def run_qa_single(dialog_text, dialog_idx, attempt=1):
    """Оценивает один диалог через Chat V3, возвращает JSON."""
    payload = {
        "model": "deepseek-v4-flash",
        "messages": [
            {"role": "system", "content": qa_prompt},
            {"role": "user", "content": f"Оцени следующий диалог и верни JSON:\n\n--- ДИАЛОГ #{dialog_idx} ---\n{dialog_text}\n"}
        ],
        "max_tokens": 4000,
        "temperature": 0.1,
        "response_format": {"type": "json_object"},
        "extra_body": {
            "thinking": {
                "type": "disabled"
            }
        }
    }
    try:
        resp = requests.post(URL, headers=headers, json=payload, timeout=300)
        if resp.status_code == 200:
            content = resp.json()['choices'][0]['message']['content']
            try:
                data = json.loads(content)
                dialogues = data.get('dialogues', [])
                return dialogues[0] if dialogues else data
            except json.JSONDecodeError as je:
                print(f"[QA] Ошибка JSON (попытка {attempt}/3): {je}")
                if attempt < 3:
                    time.sleep(2)
                    return run_qa_single(dialog_text, dialog_idx, attempt + 1)
                else:
                    return None
        elif resp.status_code == 429:
            print(f"[QA] Rate limit (попытка {attempt}/3), ждём 15 сек...")
            time.sleep(15)
            return run_qa_single(dialog_text, dialog_idx, attempt)
        else:
            print(f"[QA] API ERROR {resp.status_code}: {resp.text[:200]} (попытка {attempt}/3)")
            if attempt < 3:
                time.sleep(2)
                return run_qa_single(dialog_text, dialog_idx, attempt + 1)
            return None
    except Exception as e:
        print(f"[QA] Ошибка: {e} (попытка {attempt}/3)")
        if attempt < 3:
            time.sleep(2)
            return run_qa_single(dialog_text, dialog_idx, attempt + 1)
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
        
        audio_path_to_push = evaluated.get('audio_path', '')
        push_report_to_supabase(
            json_path=tmp_path,
            shop_id=SHOP_ID,
            audio_path=audio_path_to_push,
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
            evaluated["dialog_index"] = idx
            evaluated["audio_path"] = item.get("audio_path", "")
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
last_second = args.skip_time
dialog_idx = args.start_idx
prev_dialog_tail = ""
all_dialogues_raw = []
all_results = []

# Загружаем существующие результаты, если они есть и мы возобновляем работу
if os.path.exists(RESULTS_FILE) and args.start_idx > 1:
    try:
        with open(RESULTS_FILE, 'r', encoding='utf-8') as f:
            existing_data = json.load(f)
            all_results = [r for r in existing_data.get("results", []) if r.get("idx") < args.start_idx]
            print(f"[*] Загружено {len(all_results)} существующих результатов из {RESULTS_FILE}")
    except Exception as e:
        print(f"[*] Не удалось загрузить существующие результаты: {e}")

if os.path.exists(RESULTS_FILE.replace('.json', '_raw.json')) and args.start_idx > 1:
    try:
        with open(RESULTS_FILE.replace('.json', '_raw.json'), 'r', encoding='utf-8') as f:
            existing_raw = json.load(f)
            all_dialogues_raw = [d for d in existing_raw if d.get("idx") < args.start_idx]
            print(f"[*] Загружено {len(all_dialogues_raw)} существующих сырых диалогов")
            if all_dialogues_raw:
                last_raw = all_dialogues_raw[-1]
                last_text = last_raw.get("text", "")
                if last_text.startswith("[ЭМОЦИИ"):
                    last_text_lines = last_text.split("\n")[1:]
                else:
                    last_text_lines = last_text.split("\n")
                last_text_lines = [l for l in last_text_lines if l.strip()]
                prev_dialog_tail = "\n".join(last_text_lines[-3:]) if last_text_lines else ""
                print(f"[*] Инициализирован хвост предыдущего диалога #{last_raw.get('idx')}:")
                print(prev_dialog_tail)
    except Exception as e:
        print(f"[*] Не удалось загрузить сырые диалоги: {e}")

consecutive_empty = 0  # Счётчик пустых ответов подряд

# Используем скользящее окно поверх транскрипта.
# Системный промпт содержит ТОЛЬКО правила (sys_content), что обеспечивает его 100% кэширование!
# Сам транскрипт передается короткими окнами в пользовательском запросе, предотвращая перегрузку Reasoner-модели.
WINDOW_SIZE = 10000  # ~2 тысячи токенов, около 15-20 минут транскрипта для лучшего кэширования и экономии

print(f"\n[ITERATOR] Старт разбора дня {DATE_FOLDER} (лимит: {MAX_DIALOGUES} диалогов)...")
print(f"[ITERATOR] Режим: СКОЛЬЗЯЩЕЕ ОКНО (размер: {WINDOW_SIZE} символов)\n")

while dialog_idx <= MAX_DIALOGUES:
    # Искусственно проверяем, не вышли ли мы за пределы (просто по последней секунде)
    if parsed_canvas and last_second > parsed_canvas[-1]["end"]:
        print("[ITERATOR] Достигнут конец транскрипта.")
        break
    
    window_text, is_end = get_window(last_second, size=WINDOW_SIZE)
    if is_end or not window_text:
        print("[ITERATOR] Достигнут конец транскрипта (окно пустое).")
        break
        
    print(f" -> [{datetime.datetime.now().strftime('%H:%M:%S')}] Запрос #{dialog_idx} | ищем после: {last_second}с")
    
    # Формируем короткий меняющийся юзер-запрос с окном транскрипта
    user_msg = f"=== ФРАГМЕНТ ТРАНСКРИПТА КОФЕЙНИ ===\n{window_text}\n\n"
    if last_second == 0:
        user_msg += "Найди ПЕРВЫЙ диалог заказа в этом фрагменте транскрипта. Выдай только его текст строго по формату."
    else:
        user_msg += f"Найди ПЕРВЫЙ диалог заказа в этом фрагменте транскрипта, который начинается строго ПОСЛЕ {last_second} секунды."
        if prev_dialog_tail:
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
                if is_end:
                    print("[ITERATOR] Получен END. Достигнут конец транскрипта.")
                    break
                else:
                    last_timecodes = re.findall(r'\[(\d+)\s*-\s*(\d+)\]', window_text)
                    if last_timecodes:
                        new_start = int(last_timecodes[-1][0])
                        if new_start > last_second:
                            print(f"[ITERATOR] Получен END, но транскрипт продолжается. Сдвигаем last_second с {last_second}с на {new_start}с...")
                            last_second = new_start
                            continue
                    print("[ITERATOR] Получен END, но транскрипт продолжается. Сдвигаем на +2000 сек.")
                    last_second += 2000
                    continue

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
            
            if not has_ending:
                print(f"    [!] Внимание: диалог не содержит маркеров конца (оплата/прощание).")

            last_second = max_time

            # GigaAM-Emo
            h = min_time // 3600
            m = (min_time % 3600) // 60
            print(f"[ITERATOR] Диалог #{dialog_idx} найден ({h}:{m:02d}, {min_time}-{max_time} сек). Эмоции...")
            emo_tag, is_conflict, cut_audio_path = get_emotion_tag(min_time, max_time)
            print(f"[EMO] {emo_tag}")
            print(f"[EMO] Аудио сохранено: {cut_audio_path}")

            final_text = f"{emo_tag}\n{answer}"
            
            all_dialogues_raw.append({
                "idx": dialog_idx,
                "min_time": min_time,
                "max_time": max_time,
                "text": final_text,
                "is_conflict_emo": is_conflict
            })

            # Отправляем в QA-очередь
            qa_queue.put({"idx": dialog_idx, "text": final_text, "audio_path": cut_audio_path})

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
