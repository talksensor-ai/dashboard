"""
Full pipeline for April 23 transcript:
1. Build canvas (shift timestamps)
2. Run Iterator (DeepSeek Reasoner) — extract dialogues
3. Run QA (DeepSeek Chat V3) — score each dialogue
4. Push to Supabase

Also tracks DeepSeek context cache hit/miss to verify savings.
"""
import os
import sys
import re
import json
import time
import requests
from dotenv import load_dotenv

# Setup paths
BASE_DIR = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(BASE_DIR, 'pipeline'))
load_dotenv(os.path.join(BASE_DIR, '.env'))

from push_to_supabase import push_report_to_supabase

API_KEY = os.environ.get("DEEPSEEK_API_KEY")
URL = "https://api.deepseek.com/chat/completions"

# Config
TRANSCRIPT_FILE = os.path.join(BASE_DIR, "21-17-23-04-2026_transcript.txt")
CANVAS_FILE = os.path.join(BASE_DIR, "daily_canvas_2026-04-23.txt")
DATE_FOLDER = "2026-04-23"
SHOP_ID = 8  # Ак мечеть
SHIFT_SECONDS = 21 * 3600 + 17 * 60  # 21:17 start = 76620 sec from midnight

# Cache tracking
cache_stats = {
    "total_requests": 0,
    "total_prompt_tokens": 0,
    "total_completion_tokens": 0,
    "total_cache_hit_tokens": 0,
    "total_cache_miss_tokens": 0,
    "total_reasoning_tokens": 0,
    "requests_log": []
}

def log_usage(step_name, usage):
    """Log token usage and cache stats from DeepSeek response."""
    prompt_tokens = usage.get("prompt_tokens", 0)
    completion_tokens = usage.get("completion_tokens", 0)
    cache_hit = usage.get("prompt_cache_hit_tokens", 0)
    cache_miss = usage.get("prompt_cache_miss_tokens", 0)
    reasoning = usage.get("completion_tokens_details", {}).get("reasoning_tokens", 0) if usage.get("completion_tokens_details") else 0
    
    cache_stats["total_requests"] += 1
    cache_stats["total_prompt_tokens"] += prompt_tokens
    cache_stats["total_completion_tokens"] += completion_tokens
    cache_stats["total_cache_hit_tokens"] += cache_hit
    cache_stats["total_cache_miss_tokens"] += cache_miss
    cache_stats["total_reasoning_tokens"] += reasoning
    
    hit_pct = (cache_hit / prompt_tokens * 100) if prompt_tokens > 0 else 0
    
    entry = {
        "step": step_name,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "cache_hit": cache_hit,
        "cache_miss": cache_miss,
        "cache_hit_pct": round(hit_pct, 1),
        "reasoning_tokens": reasoning
    }
    cache_stats["requests_log"].append(entry)
    
    print(f"  [TOKENS] Tokens: prompt={prompt_tokens}, completion={completion_tokens}, "
          f"cache_hit={cache_hit} ({hit_pct:.1f}%), cache_miss={cache_miss}, reasoning={reasoning}")


def shift_timestamps_in_text(raw_text, shift_sec):
    """Adds shift_sec to all [start - end] timestamps."""
    lines = raw_text.split('\n')
    new_lines = []
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


# ==================== STEP 1: BUILD CANVAS ====================
print("\n" + "="*60)
print("STEP 1: Building daily canvas (original timestamps)...")
print("="*60)

# Use ORIGINAL timestamps (0-3600) — large shifted numbers (76000+) confuse Reasoner
# We'll note the real time offset for reference only
with open(TRANSCRIPT_FILE, 'r', encoding='utf-8') as f:
    raw_text = f.read()

# Filter out the GigaAM header lines, keep only [timestamp] lines
lines = raw_text.split('\n')
clean_lines = []
for line in lines:
    line = line.strip()
    if re.match(r'^\[\d+', line):
        clean_lines.append(line)

canvas_text = "\n".join(clean_lines)

with open(CANVAS_FILE, 'w', encoding='utf-8') as f:
    f.write(f"=== Запись кофейни Ак мечеть, {DATE_FOLDER}, начало в 21:17 ===\n")
    f.write(f"=== Таймкоды в секундах от начала записи (0 = 21:17) ===\n\n")
    f.write(canvas_text)

print(f"Canvas saved: {CANVAS_FILE}")
print(f"   Lines: {len(clean_lines)}, chars: {len(canvas_text)}")


# ==================== STEP 2: RUN ITERATOR (DeepSeek Reasoner) ====================
print("\n" + "="*60)
print("STEP 2: Running Iterator (DeepSeek Reasoner)...")
print("="*60)

# Load prompts
iterator_path = os.path.join(BASE_DIR, 'docs', 'iterator_prompt.md')
with open(iterator_path, 'r', encoding='utf-8') as f:
    base_prompt = f.read()

glossary_path = os.path.join(BASE_DIR, 'pipeline', 'glossary.json')
if os.path.exists(glossary_path):
    with open(glossary_path, 'r', encoding='utf-8') as f:
        base_prompt += "\n\nГЛОССАРИЙ:\n" + f.read()

with open(CANVAS_FILE, 'r', encoding='utf-8') as f:
    daily_transcript = f.read()

sys_content = base_prompt + "\n\n=== ТРАНСКРИПТ КОФЕЙНИ ===\n\n" + daily_transcript

headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {API_KEY}'}

last_second = 0
dialog_idx = 0
extracted_dialogs = []

print(f"\n[SYS] System prompt size: ~{len(sys_content)} chars")
print("Starting iterative dialogue extraction...\n")

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
    
    print(f"\n>>> Requesting dialog after {last_second} sec...")
    try:
        resp = requests.post(URL, headers=headers, json=payload, timeout=300)
        if resp.status_code == 200:
            resp_json = resp.json()
            # DeepSeek Reasoner may return content in 'content' or 'reasoning_content'
            choice = resp_json['choices'][0]['message']
            answer = (choice.get('content') or '').strip()
            reasoning = (choice.get('reasoning_content') or '')
            
            # Log cache usage
            if 'usage' in resp_json:
                log_usage(f"Iterator #{dialog_idx+1}", resp_json['usage'])
            
            if not answer or answer.strip() == "END" or "END" in answer[-10:]:
                print("Iterator returned END. Day complete.\n")
                break
            
            # Extract max timestamp
            times = re.findall(r'\[(\d+)\s*-\s*(\d+)\]', answer)
            if times:
                end_times = [int(t[1]) for t in times]
                max_time = max(end_times)
                
                if max_time <= last_second:
                    print(f"  ⚠️ Extracted time {max_time} <= {last_second}. Advancing +30 sec.")
                    last_second += 30
                else:
                    last_second = max_time
                
                dialog_idx += 1
                extracted_dialogs.append(answer)
                print(f"  Dialog #{dialog_idx} extracted (up to {last_second} sec)")
                
                # Print first 200 chars preview
                preview = answer[:200].replace('\n', ' | ')
                print(f"  Preview: {preview}...")
                
                # Small delay to help cache warm up
                time.sleep(1)
            else:
                print(f"  No timestamps found in response. Breaking.")
                print(f"  Response: {answer[:300]}")
                break
        elif resp.status_code == 429:
            print(f"  Rate limited. Waiting 10 sec...")
            time.sleep(10)
            continue
        else:
            print(f"  API Error {resp.status_code}: {resp.text[:300]}")
            break
    except Exception as e:
        print(f"  Exception: {e}")
        break

print(f"\nTotal dialogs extracted: {dialog_idx}")


# ==================== STEP 3: RUN QA (DeepSeek Chat V3) — BATCH BY 2 ====================
print("\n" + "="*60)
print("STEP 3: Running QA Audit (DeepSeek Chat V3, batch=2)...")
print("="*60)

qa_path = os.path.join(BASE_DIR, 'docs', 'qa_prompt.md')
with open(qa_path, 'r', encoding='utf-8') as f:
    qa_instruction = f.read()

if os.path.exists(glossary_path):
    with open(glossary_path, 'r', encoding='utf-8') as f:
        qa_instruction += "\n\nГЛОССАРИЙ:\n" + f.read()

all_qa_dialogs = []
QA_BATCH = 2

# Group dialogues into batches of 2
batches = []
for i in range(0, len(extracted_dialogs), QA_BATCH):
    batches.append(extracted_dialogs[i:i+QA_BATCH])

for batch_idx, batch in enumerate(batches):
    batch_start = batch_idx * QA_BATCH + 1
    batch_end = batch_start + len(batch) - 1
    label = f"#{batch_start}" if len(batch) == 1 else f"#{batch_start}-{batch_end}"
    print(f"\n[QA] Scoring batch {label} ({len(batch)} dialogues)...")
    
    if len(batch) == 1:
        user_content = batch[0]
    else:
        parts = []
        for i, dt in enumerate(batch):
            parts.append(f"=== ДИАЛОГ #{batch_start + i} ===\n{dt}")
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
    
    try:
        resp = requests.post(URL, headers=headers, json=payload, timeout=120)
        if resp.status_code == 200:
            resp_json = resp.json()
            json_content = resp_json['choices'][0]['message']['content']
            
            # Log cache usage
            if 'usage' in resp_json:
                log_usage(f"QA batch {label}", resp_json['usage'])
            
            # Parse JSON
            match = re.search(r'```json\s*(.*?)\s*```', json_content, re.DOTALL)
            json_str = match.group(1) if match else json_content.strip()
            
            parsed = json.loads(json_str)
            if "dialogues" not in parsed:
                parsed = {"dialogues": [parsed]}
            
            all_qa_dialogs.extend(parsed["dialogues"])
            
            # Print scores
            for d in parsed["dialogues"]:
                qa = d.get("qa_evaluation", {})
                dtype = d.get("dialogue_type", "?")
                scores = [qa.get(k, 0) for k in ["greeting_score", "order_taking_score", 
                          "upsell_score", "loyalty_score", "farewell_score", "order_duplication_score"]]
                valid = [s for s in scores if s and s > 0]
                avg = sum(valid) / len(valid) if valid else 0
                print(f"  [OK] Type: {dtype} | Scores: G={scores[0]} O={scores[1]} U={scores[2]} "
                      f"L={scores[3]} F={scores[4]} D={scores[5]} | Avg: {avg:.1f}")
        else:
            print(f"  [ERR] API Error {resp.status_code}: {resp.text[:300]}")
    except json.JSONDecodeError as e:
        print(f"  [ERR] JSON parse error: {e}")
        print(f"  Raw response: {json_content[:500]}")
    except Exception as e:
        print(f"  [ERR] Exception: {e}")



# ==================== STEP 4: PUSH TO SUPABASE ====================
print("\n" + "="*60)
print("STEP 4: Pushing to Supabase...")
print("="*60)

DRY_RUN = True  # Set to False to actually push to Supabase

if all_qa_dialogs:
    final_report = {"dialogues": all_qa_dialogs}
    report_path = os.path.join(BASE_DIR, f"FINAL_AUDIT_REPORT_23_april.json")
    
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(final_report, f, ensure_ascii=False, indent=2)
    
    print(f"[REPORT] Report saved: {report_path} ({len(all_qa_dialogs)} dialogues)")
    
    if DRY_RUN:
        print("[DRY_RUN] Skipping Supabase push (data already exists for this date)")
    else:
        print(f"[PUSH] Pushing {len(all_qa_dialogs)} dialogues to Supabase...")
        push_report_to_supabase(report_path, shop_id=SHOP_ID, audio_path="", date_folder=DATE_FOLDER)
        print("[DONE] Push complete!")
else:
    print("[WARN] No dialogues to push.")


# ==================== STEP 5: CACHE STATS REPORT ====================
print("\n" + "="*60)
print("DEEPSEEK CACHE SAVINGS REPORT")
print("="*60)

total_hit = cache_stats["total_cache_hit_tokens"]
total_miss = cache_stats["total_cache_miss_tokens"]
total_prompt = cache_stats["total_prompt_tokens"]
total_completion = cache_stats["total_completion_tokens"]
total_reasoning = cache_stats["total_reasoning_tokens"]

overall_hit_pct = (total_hit / total_prompt * 100) if total_prompt > 0 else 0

print(f"\n[STATS] Total API requests: {cache_stats['total_requests']}")
print(f"[STATS] Total prompt tokens: {total_prompt:,}")
print(f"[STATS] Total completion tokens: {total_completion:,}")
print(f"[STATS] Total reasoning tokens: {total_reasoning:,}")
print(f"\n[HIT] Cache HIT tokens: {total_hit:,}")
print(f"[MISS] Cache MISS tokens: {total_miss:,}")
print(f"[RATE] Overall cache hit rate: {overall_hit_pct:.1f}%")

# DeepSeek pricing (unified for both deepseek-chat and deepseek-reasoner):
# 1M INPUT TOKENS (CACHE HIT):  $0.028
# 1M INPUT TOKENS (CACHE MISS): $0.28
# 1M OUTPUT TOKENS:              $0.42
PRICE_HIT = 0.028
PRICE_MISS = 0.28
PRICE_OUTPUT = 0.42

# Estimate costs
reasoner_requests = [r for r in cache_stats["requests_log"] if "Iterator" in r["step"]]
chat_requests = [r for r in cache_stats["requests_log"] if "QA" in r["step"]]

# Reasoner costs
r_hit = sum(r["cache_hit"] for r in reasoner_requests)
r_miss = sum(r["cache_miss"] for r in reasoner_requests)
r_output = sum(r["completion_tokens"] for r in reasoner_requests)

cost_r_actual = (r_hit * PRICE_HIT + r_miss * PRICE_MISS + r_output * PRICE_OUTPUT) / 1_000_000
cost_r_no_cache = ((r_hit + r_miss) * PRICE_MISS + r_output * PRICE_OUTPUT) / 1_000_000

# Chat costs
c_hit = sum(r["cache_hit"] for r in chat_requests)
c_miss = sum(r["cache_miss"] for r in chat_requests)
c_output = sum(r["completion_tokens"] for r in chat_requests)

cost_c_actual = (c_hit * PRICE_HIT + c_miss * PRICE_MISS + c_output * PRICE_OUTPUT) / 1_000_000
cost_c_no_cache = ((c_hit + c_miss) * PRICE_MISS + c_output * PRICE_OUTPUT) / 1_000_000

total_actual = cost_r_actual + cost_c_actual
total_no_cache = cost_r_no_cache + cost_c_no_cache
savings = total_no_cache - total_actual

print(f"\n[COST] COST ESTIMATION:")
print(f"   Reasoner: ${cost_r_actual:.4f} (without cache: ${cost_r_no_cache:.4f})")
print(f"   Chat V3:  ${cost_c_actual:.4f} (without cache: ${cost_c_no_cache:.4f})")
print(f"   ----------------------------")
print(f"   TOTAL:    ${total_actual:.4f}")
print(f"   Without cache would be: ${total_no_cache:.4f}")
print(f"   SAVINGS: ${savings:.4f} ({(savings/total_no_cache*100) if total_no_cache > 0 else 0:.1f}%)")

print("\n[DETAIL] Per-request breakdown:")
for r in cache_stats["requests_log"]:
    print(f"   {r['step']:20s} | prompt: {r['prompt_tokens']:6d} | "
          f"hit: {r['cache_hit']:6d} ({r['cache_hit_pct']:5.1f}%) | "
          f"miss: {r['cache_miss']:6d} | completion: {r['completion_tokens']:5d}")

# Save full stats
stats_path = os.path.join(BASE_DIR, "cache_stats_23_april.json")
with open(stats_path, 'w', encoding='utf-8') as f:
    json.dump(cache_stats, f, ensure_ascii=False, indent=2)
print(f"\n[FILE] Full stats saved: {stats_path}")
print("\n[DONE] Pipeline complete!")
