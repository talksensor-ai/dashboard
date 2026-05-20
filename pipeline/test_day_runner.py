"""
TEST DAY RUNNER — 24 апреля 2026
================================
Полный цикл обработки за день:
  Yandex Disk → GigaAM → DeepSeek Reasoner (Iterator) → DeepSeek Chat (QA batch=2) → Supabase

Запуск: python test_day_runner.py
Остановка: Ctrl+C (сформирует финальный отчёт)

Логирует ВСЁ:
- Кол-во файлов / диалогов
- Токены (prompt/completion/cache hit/miss/reasoning)
- Стоимость каждого запроса
- Время обработки каждого этапа
- Ошибки и затыки
- Нагрузка GPU (при транскрибации)
"""
import os
import sys
import time
import json
import re
import datetime
import requests
import traceback
from dotenv import load_dotenv

# Setup
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
PIPELINE_DIR = os.path.dirname(__file__)
sys.path.insert(0, PIPELINE_DIR)

load_dotenv(os.path.join(BASE_DIR, '.env'))

import yadisk
from audio_audit_pipeline import run_gigaam
from daily_cache_worker import (
    shift_timestamps_in_text, timestamp_to_seconds,
    run_cache_iterator, run_qa_on_batch, _load_qa_prompt, QA_BATCH_SIZE
)
from push_to_supabase import push_report_to_supabase

# ==================== CONFIG ====================
TEST_DATE = "2026-04-24"
CAFE_FOLDER = "/Ак мечеть"
SHOP_ID = 8
POLL_INTERVAL = 600  # Проверяем новые файлы каждые 10 минут
API_KEY = os.environ.get("DEEPSEEK_API_KEY")
API_URL = "https://api.deepseek.com/chat/completions"

# DeepSeek pricing
PRICE_HIT = 0.028     # $/1M tokens
PRICE_MISS = 0.28
PRICE_OUTPUT = 0.42

LOG_FILE = os.path.join(BASE_DIR, f"test_day_{TEST_DATE}_log.json")
REPORT_FILE = os.path.join(BASE_DIR, f"test_day_{TEST_DATE}_report.md")

# ==================== ANALYTICS STATE ====================
analytics = {
    "test_date": TEST_DATE,
    "start_time": None,
    "end_time": None,
    "shop": "Ак мечеть",
    "shop_id": SHOP_ID,
    
    # Files
    "audio_files_total": 0,
    "audio_files_processed": [],
    "audio_files_skipped": [],
    "audio_files_failed": [],
    
    # GigaAM
    "gigaam_total_time_sec": 0,
    "gigaam_runs": [],
    
    # Iterator (Reasoner)
    "iterator_total_calls": 0,
    "iterator_total_dialogues": 0,
    "iterator_api_calls": [],
    
    # QA (Chat V3)
    "qa_total_calls": 0,
    "qa_total_dialogues_scored": 0,
    "qa_api_calls": [],
    
    # Tokens
    "total_prompt_tokens": 0,
    "total_completion_tokens": 0,
    "total_cache_hit_tokens": 0,
    "total_cache_miss_tokens": 0,
    "total_reasoning_tokens": 0,
    
    # Cost
    "total_cost_usd": 0,
    "cost_without_cache_usd": 0,
    
    # Supabase
    "supabase_pushes": 0,
    "supabase_errors": 0,
    
    # Errors
    "errors": [],
    
    # Per-hour breakdown
    "hourly_stats": {}
}


def save_log():
    """Save analytics to JSON log file."""
    with open(LOG_FILE, 'w', encoding='utf-8') as f:
        json.dump(analytics, f, ensure_ascii=False, indent=2, default=str)


def log_error(stage, message, file_name=""):
    """Log an error."""
    entry = {
        "time": datetime.datetime.now().isoformat(),
        "stage": stage,
        "file": file_name,
        "message": str(message)
    }
    analytics["errors"].append(entry)
    print(f"[ERROR] [{stage}] {file_name}: {message}")
    save_log()


def log_api_call(stage, file_name, usage, elapsed_sec):
    """Log a DeepSeek API call with full token details."""
    prompt = usage.get("prompt_tokens", 0)
    completion = usage.get("completion_tokens", 0)
    cache_hit = usage.get("prompt_cache_hit_tokens", 0)
    cache_miss = usage.get("prompt_cache_miss_tokens", 0)
    reasoning = 0
    if usage.get("completion_tokens_details"):
        reasoning = usage["completion_tokens_details"].get("reasoning_tokens", 0)
    
    # Costs
    cost = (cache_hit * PRICE_HIT + cache_miss * PRICE_MISS + completion * PRICE_OUTPUT) / 1_000_000
    cost_no_cache = ((cache_hit + cache_miss) * PRICE_MISS + completion * PRICE_OUTPUT) / 1_000_000
    
    entry = {
        "time": datetime.datetime.now().isoformat(),
        "stage": stage,
        "file": file_name,
        "prompt_tokens": prompt,
        "completion_tokens": completion,
        "cache_hit": cache_hit,
        "cache_miss": cache_miss,
        "reasoning_tokens": reasoning,
        "cost_usd": round(cost, 6),
        "elapsed_sec": round(elapsed_sec, 1)
    }
    
    if "Iterator" in stage or "Reasoner" in stage:
        analytics["iterator_api_calls"].append(entry)
        analytics["iterator_total_calls"] += 1
    else:
        analytics["qa_api_calls"].append(entry)
        analytics["qa_total_calls"] += 1
    
    analytics["total_prompt_tokens"] += prompt
    analytics["total_completion_tokens"] += completion
    analytics["total_cache_hit_tokens"] += cache_hit
    analytics["total_cache_miss_tokens"] += cache_miss
    analytics["total_reasoning_tokens"] += reasoning
    analytics["total_cost_usd"] += cost
    analytics["cost_without_cache_usd"] += cost_no_cache
    
    hit_pct = (cache_hit / prompt * 100) if prompt > 0 else 0
    print(f"  [API] {stage} | tokens:{prompt}+{completion} | cache:{hit_pct:.0f}% | ${cost:.4f} | {elapsed_sec:.1f}s")


def process_audio_file(y, file_name, target_path):
    """Process a single audio file through the full pipeline."""
    hour_key = file_name.replace('.ogg', '')
    hour_stats = {
        "file": file_name,
        "start_time": datetime.datetime.now().isoformat(),
        "gigaam_time_sec": 0,
        "dialogues_found": 0,
        "dialogues_scored": 0,
        "iterator_calls": 0,
        "qa_calls": 0,
        "cost_usd": 0,
        "errors": []
    }
    
    local_ogg = os.path.join(BASE_DIR, f"{TEST_DATE}_{file_name}")
    local_txt = local_ogg.replace('.ogg', '_transcript.txt')
    canvas_file = os.path.join(BASE_DIR, f"canvas_{TEST_DATE}_{hour_key}.txt")
    
    cost_before = analytics["total_cost_usd"]
    
    try:
        # ===== STEP 1: DOWNLOAD =====
        if not os.path.exists(local_ogg):
            print(f"\n[DOWNLOAD] {file_name}...")
            dl_start = time.time()
            y.download(f"{target_path}/{file_name}", local_ogg)
            dl_time = time.time() - dl_start
            fsize = os.path.getsize(local_ogg)
            print(f"  Downloaded: {fsize / 1024 / 1024:.1f} MB in {dl_time:.1f}s")
            
            if fsize < 1024:
                log_error("download", f"File too small ({fsize} bytes), corrupted?", file_name)
                analytics["audio_files_skipped"].append(file_name)
                os.remove(local_ogg)
                return
        else:
            print(f"\n[DOWNLOAD] {file_name} already exists locally")
        
        # ===== STEP 2: GIGAAM TRANSCRIPTION =====
        if not os.path.exists(local_txt):
            print(f"[GIGAAM] Transcribing {file_name}...")
            giga_start = time.time()
            run_gigaam(local_ogg, local_txt)
            giga_time = time.time() - giga_start
            hour_stats["gigaam_time_sec"] = round(giga_time, 1)
            analytics["gigaam_total_time_sec"] += giga_time
            analytics["gigaam_runs"].append({
                "file": file_name,
                "time_sec": round(giga_time, 1),
                "timestamp": datetime.datetime.now().isoformat()
            })
            print(f"  Transcribed in {giga_time:.1f}s")
        else:
            print(f"[GIGAAM] Transcript already exists: {local_txt}")
        
        # ===== STEP 3: BUILD CANVAS =====
        if not os.path.exists(canvas_file):
            with open(local_txt, 'r', encoding='utf-8') as f:
                raw_text = f.read()
            
            # Filter to timestamp lines only
            lines = raw_text.split('\n')
            clean_lines = [l.strip() for l in lines if re.match(r'^\[\d+', l.strip())]
            
            with open(canvas_file, 'w', encoding='utf-8') as f:
                f.write(f"=== {file_name}, дата {TEST_DATE} ===\n")
                f.write(f"=== Таймкоды в секундах от начала записи ===\n\n")
                f.write("\n".join(clean_lines))
            
            print(f"[CANVAS] Built: {len(clean_lines)} lines")
        
        # ===== STEP 4: ITERATOR (DeepSeek Reasoner) =====
        print(f"[ITERATOR] Extracting dialogues from {file_name}...")
        
        iterator_p = os.path.join(BASE_DIR, 'docs', 'iterator_prompt.md')
        with open(iterator_p, 'r', encoding='utf-8') as f:
            base_prompt = f.read()
        
        glossary_path = os.path.join(PIPELINE_DIR, 'glossary.json')
        if os.path.exists(glossary_path):
            with open(glossary_path, 'r', encoding='utf-8') as f:
                base_prompt += "\n\nГЛОССАРИЙ:\n" + f.read()
        
        with open(canvas_file, 'r', encoding='utf-8') as f:
            canvas_text = f.read()
            
        # --- ТЕКСТОВЫЙ НАХЛЕСТ (TEXT OVERLAP) ---
        # Find the previous transcript file to provide context for the boundary
        try:
            txt_files = [f for f in os.listdir(BASE_DIR) if f.endswith('_transcript.txt') and TEST_DATE in f]
            txt_files.sort()
            current_idx = txt_files.index(f"{TEST_DATE}_{file_name.replace('.ogg', '_transcript.txt')}")
            if current_idx > 0:
                prev_txt = os.path.join(BASE_DIR, txt_files[current_idx - 1])
                with open(prev_txt, 'r', encoding='utf-8') as f_prev:
                    prev_lines = f_prev.read().strip().split('\n')
                    # Get the last 30 lines (approx 5-10 minutes of speech)
                    overlap_text = "\n".join(prev_lines[-30:])
                    canvas_text = f"=== КОНЕЦ ПРЕДЫДУЩЕГО ЧАСА (КОНТЕКСТ) ===\n{overlap_text}\n\n=== ТЕКУЩИЙ ЧАС ===\n{canvas_text}"
                print(f"[CANVAS] Appended 30 lines of overlap from {txt_files[current_idx - 1]}")
        except Exception as e:
            print(f"[CANVAS] Overlap failed: {e}")
        
        sys_content = base_prompt + "\n\n=== ТРАНСКРИПТ КОФЕЙНИ ===\n\n" + canvas_text
        headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {API_KEY}'}
        
        last_second = 0
        dialog_idx = 0
        extracted_dialogs = []
        
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
            
            iter_start = time.time()
            try:
                resp = requests.post(API_URL, headers=headers, json=payload, timeout=300)
                iter_elapsed = time.time() - iter_start
                
                if resp.status_code == 200:
                    resp_json = resp.json()
                    choice = resp_json['choices'][0]['message']
                    answer = (choice.get('content') or '').strip()
                    
                    if 'usage' in resp_json:
                        log_api_call(f"Reasoner/{file_name}", file_name, resp_json['usage'], iter_elapsed)
                    
                    hour_stats["iterator_calls"] += 1
                    
                    if not answer or answer.strip() == "END" or "END" in answer[-10:]:
                        print(f"  [ITERATOR] END after {dialog_idx} dialogues")
                        break
                    
                    times = re.findall(r'\[(\d+)\s*-\s*(\d+)\]', answer)
                    if times:
                        max_time = max(int(t[1]) for t in times)
                        if max_time <= last_second:
                            last_second += 30
                        else:
                            last_second = max_time
                        
                        dialog_idx += 1
                        extracted_dialogs.append(answer)
                        print(f"  [ITERATOR] Dialog #{dialog_idx} (up to {last_second}s)")
                    else:
                        print(f"  [ITERATOR] No timestamps. Breaking.")
                        break
                    
                    time.sleep(1)
                    
                elif resp.status_code == 429:
                    print("  [ITERATOR] Rate limited, waiting 15s...")
                    time.sleep(15)
                    continue
                else:
                    log_error("iterator", f"API {resp.status_code}: {resp.text[:200]}", file_name)
                    break
            except Exception as e:
                log_error("iterator", str(e), file_name)
                break
        
        hour_stats["dialogues_found"] = dialog_idx
        analytics["iterator_total_dialogues"] += dialog_idx
        
        # ===== STEP 5: QA (DeepSeek Chat V3, batch=2) =====
        if extracted_dialogs:
            print(f"[QA] Scoring {len(extracted_dialogs)} dialogues (batch={QA_BATCH_SIZE})...")
            
            qa_instruction = _load_qa_prompt()
            all_qa_results = []
            
            for i in range(0, len(extracted_dialogs), QA_BATCH_SIZE):
                batch = extracted_dialogs[i:i+QA_BATCH_SIZE]
                batch_start = i + 1
                
                if len(batch) == 1:
                    user_content = batch[0]
                else:
                    parts = [f"=== ДИАЛОГ #{batch_start + j} ===\n{dt}" for j, dt in enumerate(batch)]
                    user_content = "\n\n".join(parts)
                
                payload = {
                    "model": "deepseek-chat",
                    "messages": [
                        {"role": "system", "content": qa_instruction},
                        {"role": "user", "content": user_content}
                    ],
                    "max_tokens": 8000,
                    "response_format": {"type": "json_object"}
                }
                
                qa_start = time.time()
                try:
                    resp = requests.post(API_URL, headers=headers, json=payload, timeout=120)
                    qa_elapsed = time.time() - qa_start
                    
                    if resp.status_code == 200:
                        resp_json = resp.json()
                        json_content = resp_json['choices'][0]['message']['content']
                        
                        if 'usage' in resp_json:
                            log_api_call(f"QA/{file_name}", file_name, resp_json['usage'], qa_elapsed)
                        
                        hour_stats["qa_calls"] += 1
                        
                        match = re.search(r'```json\s*(.*?)\s*```', json_content, re.DOTALL)
                        json_str = match.group(1) if match else json_content.strip()
                        
                        parsed = json.loads(json_str)
                        if "dialogues" not in parsed:
                            parsed = {"dialogues": [parsed]}
                        
                        all_qa_results.extend(parsed["dialogues"])
                        
                        for d in parsed["dialogues"]:
                            qa = d.get("qa_evaluation", {})
                            scores = [qa.get(k, 0) or 0 for k in [
                                "greeting_score", "order_taking_score", "upsell_score",
                                "loyalty_score", "farewell_score", "order_duplication_score"
                            ]]
                            valid = [s for s in scores if s > 0]
                            avg = sum(valid) / len(valid) if valid else 0
                            print(f"    Scores: G={scores[0]} O={scores[1]} U={scores[2]} "
                                  f"L={scores[3]} F={scores[4]} D={scores[5]} | Avg={avg:.1f}")
                    
                    elif resp.status_code == 429:
                        print("  [QA] Rate limited, waiting 15s...")
                        time.sleep(15)
                    else:
                        log_error("qa", f"API {resp.status_code}", file_name)
                        
                except json.JSONDecodeError as e:
                    log_error("qa_parse", str(e), file_name)
                except Exception as e:
                    log_error("qa", str(e), file_name)
            
            hour_stats["dialogues_scored"] = len(all_qa_results)
            analytics["qa_total_dialogues_scored"] += len(all_qa_results)
            
            # ===== STEP 6: PUSH TO SUPABASE =====
            if all_qa_results:
                report = {"dialogues": all_qa_results}
                report_path = os.path.join(BASE_DIR, f"report_{TEST_DATE}_{hour_key}.json")
                with open(report_path, 'w', encoding='utf-8') as f:
                    json.dump(report, f, ensure_ascii=False, indent=2)
                
                try:
                    push_report_to_supabase(
                        report_path, 
                        shop_id=SHOP_ID, 
                        audio_path=local_ogg,
                        date_folder=TEST_DATE,
                        shop_name="ak-mechet"
                    )
                    analytics["supabase_pushes"] += 1
                    print(f"  [SUPABASE] Pushed {len(all_qa_results)} dialogues (with audio)")
                except Exception as e:
                    analytics["supabase_errors"] += 1
                    log_error("supabase", str(e), file_name)
    
    except Exception as e:
        log_error("pipeline", f"{traceback.format_exc()}", file_name)
        analytics["audio_files_failed"].append(file_name)
    
    hour_stats["cost_usd"] = round(analytics["total_cost_usd"] - cost_before, 4)
    hour_stats["end_time"] = datetime.datetime.now().isoformat()
    analytics["hourly_stats"][hour_key] = hour_stats
    analytics["audio_files_processed"].append(file_name)
    save_log()


def generate_report():
    """Generate the final markdown report."""
    a = analytics
    total_time = 0
    if a["start_time"] and a["end_time"]:
        start = datetime.datetime.fromisoformat(a["start_time"])
        end = datetime.datetime.fromisoformat(a["end_time"])
        total_time = (end - start).total_seconds()
    
    cache_pct = (a["total_cache_hit_tokens"] / a["total_prompt_tokens"] * 100) if a["total_prompt_tokens"] > 0 else 0
    savings = a["cost_without_cache_usd"] - a["total_cost_usd"]
    
    report = f"""# Test Day Report: {TEST_DATE}
## Кофейня: Ак мечеть (shop_id={SHOP_ID})

---

## Общая сводка

| Метрика | Значение |
|---|---|
| Время работы | {total_time/3600:.1f} часов |
| Аудиофайлов обработано | {len(a['audio_files_processed'])} |
| Аудиофайлов пропущено | {len(a['audio_files_skipped'])} |
| Аудиофайлов с ошибкой | {len(a['audio_files_failed'])} |
| **Диалогов найдено** | **{a['iterator_total_dialogues']}** |
| **Диалогов оценено** | **{a['qa_total_dialogues_scored']}** |
| Записей в Supabase | {a['supabase_pushes']} |
| Ошибок | {len(a['errors'])} |

## GigaAM (транскрибация)

| Метрика | Значение |
|---|---|
| Всего запусков | {len(a['gigaam_runs'])} |
| Общее время | {a['gigaam_total_time_sec']/60:.1f} мин |
| Среднее на файл | {a['gigaam_total_time_sec']/max(len(a['gigaam_runs']),1):.0f} сек |

"""
    # GigaAM per-file
    if a['gigaam_runs']:
        report += "### По файлам:\n| Файл | Время (сек) |\n|---|---|\n"
        for run in a['gigaam_runs']:
            report += f"| {run['file']} | {run['time_sec']} |\n"
        report += "\n"

    report += f"""## DeepSeek API

### Токены

| Метрика | Значение |
|---|---|
| Prompt tokens | {a['total_prompt_tokens']:,} |
| Completion tokens | {a['total_completion_tokens']:,} |
| Reasoning tokens | {a['total_reasoning_tokens']:,} |
| Cache HIT | {a['total_cache_hit_tokens']:,} ({cache_pct:.1f}%) |
| Cache MISS | {a['total_cache_miss_tokens']:,} |

### Вызовы API

| Компонент | Вызовов |
|---|---|
| Iterator (Reasoner) | {a['iterator_total_calls']} |
| QA (Chat V3, batch=2) | {a['qa_total_calls']} |
| **Всего** | **{a['iterator_total_calls'] + a['qa_total_calls']}** |

### Стоимость

| | Сумма |
|---|---|
| С кешем | **${a['total_cost_usd']:.4f}** |
| Без кеша было бы | ${a['cost_without_cache_usd']:.4f} |
| Экономия кеша | ${savings:.4f} ({(savings/max(a['cost_without_cache_usd'],0.0001)*100):.1f}%) |
| В рублях (~78 руб/$) | {a['total_cost_usd']*78:.2f} руб |

## По часам

| Файл | Диалогов | QA батчей | GigaAM (сек) | Стоимость |
|---|---|---|---|---|
"""
    for key, hs in sorted(a["hourly_stats"].items()):
        report += f"| {hs['file']} | {hs['dialogues_found']} | {hs['qa_calls']} | {hs['gigaam_time_sec']} | ${hs['cost_usd']:.4f} |\n"

    if a["errors"]:
        report += f"\n## Ошибки ({len(a['errors'])})\n\n"
        for err in a["errors"]:
            report += f"- **[{err['stage']}]** {err['file']}: {err['message'][:200]}\n"
    
    report += f"\n---\n*Отчёт сформирован: {datetime.datetime.now().isoformat()}*\n"
    
    with open(REPORT_FILE, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n[REPORT] Saved: {REPORT_FILE}")
    return report


# ==================== MAIN LOOP ====================
def main():
    TOKEN = os.environ.get("YANDEX_TOKEN")
    if not TOKEN:
        print("YANDEX_TOKEN missing in .env!")
        sys.exit(1)
    
    ya = yadisk.YaDisk(token=TOKEN)
    target_path = f"{CAFE_FOLDER}/{TEST_DATE}"
    
    analytics["start_time"] = datetime.datetime.now().isoformat()
    processed_files = set()
    
    print("=" * 60)
    print(f"  TEST DAY RUNNER: {TEST_DATE}")
    print(f"  Shop: {CAFE_FOLDER} (ID={SHOP_ID})")
    print(f"  Poll interval: {POLL_INTERVAL}s")
    print(f"  Log: {LOG_FILE}")
    print("=" * 60)
    print(f"\nWaiting for audio files in {target_path}...")
    print("Press Ctrl+C to stop and generate report.\n")
    
    save_log()
    
    try:
        while True:
            try:
                # Check for new files
                items = list(ya.listdir(target_path))
                oggs = sorted([
                    i.name for i in items 
                    if i.type == 'file' and i.name.endswith('.ogg')
                ])
                
                analytics["audio_files_total"] = len(oggs)
                new_files = [f for f in oggs if f not in processed_files]
                
                if new_files:
                    print(f"\n[SCAN] Found {len(new_files)} new file(s): {', '.join(new_files)}")
                    
                    for fname in new_files:
                        print(f"\n{'='*50}")
                        print(f"  PROCESSING: {fname}")
                        print(f"{'='*50}")
                        
                        process_audio_file(ya, fname, target_path)
                        processed_files.add(fname)
                        
                        print(f"\n[STATUS] Processed: {len(processed_files)}/{len(oggs)} | "
                              f"Dialogues: {analytics['iterator_total_dialogues']} | "
                              f"Cost: ${analytics['total_cost_usd']:.4f}")
                else:
                    now = datetime.datetime.now().strftime("%H:%M")
                    print(f"[{now}] No new files. {len(processed_files)} processed, "
                          f"{analytics['iterator_total_dialogues']} dialogues, "
                          f"${analytics['total_cost_usd']:.4f} spent. "
                          f"Next check in {POLL_INTERVAL}s...")
                
                save_log()
                time.sleep(POLL_INTERVAL)
                
            except yadisk.exceptions.PathNotFoundError:
                now = datetime.datetime.now().strftime("%H:%M")
                print(f"[{now}] Folder {target_path} not found yet. Waiting...")
                time.sleep(POLL_INTERVAL)
            except Exception as e:
                log_error("main_loop", str(e))
                time.sleep(30)
    
    except KeyboardInterrupt:
        print("\n\n[STOP] Ctrl+C received. Generating final report...")
    
    # Final cleanup
    analytics["end_time"] = datetime.datetime.now().isoformat()
    save_log()
    
    # Generate report
    report = generate_report()
    print("\n" + "=" * 60)
    print(report)
    print("=" * 60)
    print(f"\nLog: {LOG_FILE}")
    print(f"Report: {REPORT_FILE}")


if __name__ == "__main__":
    main()
