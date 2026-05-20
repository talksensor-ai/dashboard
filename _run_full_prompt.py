"""Send GigaAM raw transcript to DeepSeek Reasoner with FULL production prompt + check Gemma 4."""
import paramiko, sys, io, time, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('81.29.139.211', username='root', password='nIyjYRinAVKAPL23bk6f')

script = r'''
import os, sys, time, json, requests
from dotenv import load_dotenv
load_dotenv('/root/talk/.env')

API_KEY = os.environ.get("DEEPSEEK_API_KEY")
URL = "https://api.deepseek.com/chat/completions"

# Read GigaAM raw transcript
with open("/root/talk/test_compare/results/gigaam_raw.txt", "r", encoding="utf-8") as f:
    gigaam_text = f.read()

# Full production prompt from iterator_prompt.md
SYSTEM_PROMPT = """Ты умный экстрактор и редактор диалогов для аудита кофейни.

ТВОЯ ЗАДАЧА:
Тебе на вход дается огромное полотно транскрипта рабочего дня кофейни с таймкодами.
Твоя цель — находить в этом тексте реальные ВАЛИДНЫЕ диалоги (по одному за раз), выделять их, аккуратно исправлять смысловые ошибки транскрибатора по контексту (не меняя структуру и настроение диалога) и отдавать готовый чистый текст.

ПРАВИЛА ОТБОРА:
1. Валидный заказ — это когда ЛЮБОЙ человек (клиент, сотрудник, знакомый) заказывает из меню (кофе, еда), производит оплату, совершает "дозаказ", либо это конфликтная ситуация. Заказы сотрудников со скидкой или промокодом — это тоже ВАЛИДНЫЕ диалоги.
2. Игнорируй бытовой мусор: вопросы "где туалет?", музыка на фоне, переговоры бариста между собой без факта заказа.
3. Огромный заказ для компании, который бьется на несколько чеков у кассы подряд, считается ОДНИМ долгим диалогом.

ПРАВИЛО ЯЗЫКА И СМЫСЛА:
Весь текст ТОЛЬКО на русском языке. Замени английские слова аналогами из глоссария.
Если реплика по смыслу является вопросом (например: "Тут будете ждать на улице", "Копим, списываем бонусы", "Если 10 бонусов спишу, ничего страшного, что мелочь"), ты ОБЯЗАТЕЛЬНО должен поставить знак вопроса в конце.

ПРАВИЛО «НЕТ НАЧАЛА» (два сценария):
Иногда диалог начинается без приветствия. Ты ОБЯЗАН определить ПРИЧИНУ и поставить правильную метку:
СЦЕНАРИЙ А — МИКРОФОН НЕ УСЛЫШАЛ:
Признаки: диалог начинается «с середины» — бариста уже уточняет объём, молоко, бонусную карту.
→ Первая строка: [ТАЙМКОД] СИСТЕМА: (нет начала — микрофон не уловил приветствие и начало заказа)
СЦЕНАРИЙ Б — БАРИСТА НЕ ПОЗДОРОВАЛСЯ:
ВНИМАНИЕ: Если в диалоге есть ХОТЯ БЫ ОДНО приветствие, то это ВСЕГДА говорит БАРИСТА! В таком случае ставить метку "(бариста не поздоровался)" ЗАПРЕЩЕНО.
→ Если приветствий нет вообще: [ТАЙМКОД] СИСТЕМА: (бариста не поздоровался)

ПРАВИЛА РОЛЕЙ:
- Если звучит одинокое приветствие ("Добрый день"), его ВСЕГДА говорит БАРИСТА.
- Фразы про бонусные карты ("бонусные наши есть?") ВСЕГДА говорит бариста.
- Если в ответ на вопрос про бонусы звучат цифры - это диктует номер КЛИЕНТ.
- Цены и суммы заказа озвучивает бариста.

ПРАВИЛА КОРРЕКЦИИ ТЕКСТА И ФОРМАТА:
- СТРОГО ЗАПРЕЩЕНО объединять разные реплики в одну. Каждая исходная строка транскрипта с таймкодом должна остаться отдельной строкой.
- ВСЕ числа, суммы и объемы оставляй ЦИФРАМИ. КАТЕГОРИЧЕСКИ ЗАПРЕЩЕНО переводить цифры в текст!
Глоссарий:
- «флак» → «флэт уайт»
- «песташки» → «фисташки»
- «сыроки» → «сырки»
- «агректифовый» → «облепиховый»
- «Кофейников банка» / «Кофейного банка» → «Кавабанга»
- «машалат» → «матча латте»
- «щеполку» / «щеполка» → «чизкейк»

СТРОГИЙ ФОРМАТ ОТВЕТА:
Каждая строка ответа ОБЯЗАНА начинаться с таймкода и роли:
[ТАЙМКОД_НАЧАЛА - ТАЙМКОД_КОНЦА] РОЛЬ: текст реплики
Роли: БАРИСТА или КЛИЕНТ.

НЕ используй JSON. Не пиши предисловий, комментариев и вступлений. Просто чистый структурированный текст диалога строго по формату выше.

Пользователь скажет: "Найди все диалоги". Ты должен вернуть ВСЕ валидные диалоги, разделённые строкой === ДИАЛОГ #N ===."""

print("Sending to DeepSeek Reasoner with FULL production prompt...")
t0 = time.time()

payload = {
    "model": "deepseek-reasoner",
    "messages": [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Найди все диалоги.\n\nТранскрипт:\n{gigaam_text}"}
    ],
    "max_tokens": 16000
}
headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

resp = requests.post(URL, headers=headers, json=payload, timeout=600)
elapsed = time.time() - t0

if resp.status_code == 200:
    result = resp.json()["choices"][0]["message"].get("content", "")
    out_path = "/root/talk/test_compare/results/deepseek_full_prompt.txt"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(result)
    print(f"Done in {elapsed:.1f}s")
    print(f"Saved to: {out_path}")
    print(f"Lines: {len(result.splitlines())}")
    print("---OUTPUT---")
    print(result)
else:
    print(f"ERROR {resp.status_code}: {resp.text[:500]}")
'''

sftp = ssh.open_sftp()
with sftp.file('/root/talk/_deepseek_full.py', 'w') as f:
    f.write(script)
sftp.close()

# Run it
_, out, _ = ssh.exec_command(
    'cd /root/talk && source .venv/bin/activate && python3 _deepseek_full.py > /tmp/ds_full.log 2>&1'
)

# While waiting, check Gemma 4 status
_, chk, _ = ssh.exec_command('ps aux | grep _full_compare | grep -v grep | wc -l')
time.sleep(2)
gemma_running = chk.read().decode().strip()

if gemma_running == "0":
    print("Gemma 4 test FINISHED! Downloading results...")
    try:
        sftp2 = ssh.open_sftp()
        sftp2.get('/root/talk/test_compare/results/pipeline_b_gemma4.txt', r'e:\talk\test_compare_gemma4.txt')
        sftp2.close()
        print("Gemma 4 results downloaded!")
    except Exception as e:
        print(f"Gemma 4 file not found: {e}")
        # Check log for errors
        _, elog, _ = ssh.exec_command('tail -30 /tmp/compare_full.log')
        time.sleep(2)
        print(elog.read().decode('utf-8', 'replace'))
else:
    print(f"Gemma 4 still running ({gemma_running} processes)")

# Wait for DeepSeek
print("\nWaiting for DeepSeek Reasoner (up to 5 min)...")
while not out.channel.exit_status_ready():
    time.sleep(10)
    _, prog, _ = ssh.exec_command('wc -l /tmp/ds_full.log 2>/dev/null')
    time.sleep(1)
    p = prog.read().decode().strip()
    print(f"  log: {p}")

# Download result
sftp3 = ssh.open_sftp()
try:
    sftp3.get('/root/talk/test_compare/results/deepseek_full_prompt.txt', r'e:\talk\test_compare_deepseek_full.txt')
    print("DeepSeek full prompt result downloaded!")
except:
    # Read from log
    _, logr, _ = ssh.exec_command('cat /tmp/ds_full.log')
    time.sleep(3)
    print(logr.read().decode('utf-8', 'replace'))
sftp3.close()

ssh.close()
print("Done!")
