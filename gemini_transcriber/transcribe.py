#!/usr/bin/env python3
"""
Gemini Transcriber — транскрибация аудио через Gemini API.

Берёт часовые OGG-файлы из локальной папки, отправляет в Gemini,
получает транскрипцию с таймкодами и склеивает в daily canvas.

Использование:
    python transcribe.py --dates 2026-06-21 2026-06-22 2026-06-23
    python transcribe.py --dates 2026-06-21  (один день)
"""

import os
import re
import sys
import time
import json
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Fix Windows console encoding
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# -- Загружаем .env -----------------------------------------------
SCRIPT_DIR = Path(__file__).parent
load_dotenv(SCRIPT_DIR / ".env")

# -- Конфигурация -------------------------------------------------
AUDIO_BASE = Path(r"E:\talk\АУДИОЗАПИСИ\Ак мечеть")
OUTPUT_DIR = SCRIPT_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

# Ротация ключей
API_KEYS = []
for i in range(1, 10):
    key = os.environ.get(f"GEMINI_KEY_{i}")
    if key:
        API_KEYS.append(key)

if not API_KEYS:
    print("[ERR] Ни одного GEMINI_KEY_* не найдено в .env!")
    sys.exit(1)

print(f"[KEY] Загружено {len(API_KEYS)} API-ключей")

# Индекс текущего ключа (глобальный)
_current_key_idx = 0


def get_next_key() -> str:
    """Ротация ключей по кругу."""
    global _current_key_idx
    key = API_KEYS[_current_key_idx % len(API_KEYS)]
    _current_key_idx += 1
    return key


def parse_ogg_start_time(filename: str) -> tuple[int, int]:
    """
    Парсит имя файла OGG -> (час, минута).
    '09-00-21-06-2026.ogg' -> (9, 0)
    '13-28-21-06-2026.ogg' -> (13, 28)
    """
    match = re.match(r"(\d{2})-(\d{2})", filename)
    if match:
        return int(match.group(1)), int(match.group(2))
    return 0, 0


def transcribe_audio_file(ogg_path: Path, file_start_hour: int, file_start_min: int) -> str | None:
    """
    Отправляет аудиофайл в Gemini и получает транскрипцию.
    Возвращает текст транскрипции или None при ошибке.
    """
    from google import genai
    from google.genai import types

    api_key = get_next_key()
    key_label = f"KEY_{(_current_key_idx - 1) % len(API_KEYS) + 1}"

    print(f"    [SEND] Отправляю в Gemini ({key_label})...", end="", flush=True)

    client = genai.Client(api_key=api_key)

    # Промпт для транскрибации
    prompt = f"""Ты — профессиональный транскрибатор. Переведи эту аудиозапись в текст.

КОНТЕКСТ: Это запись из кофейни в Крыму. Бариста и клиенты общаются на русском языке, 
но используют крымскотатарские приветствия: "Селям алейкум", "Алейкум селям", "Сагъ ол" (спасибо), 
"Мерхаба" (здравствуйте). Также встречаются названия напитков: латте, капучино, флет-уайт, 
раф, эспрессо, американо, джезве.

ВАЖНО: Запись начинается в {file_start_hour:02d}:{file_start_min:02d}. 
Используй РЕАЛЬНОЕ время в таймкодах.

ФОРМАТ ВЫВОДА (строго!):
[ЧЧ:ММ:СС - ЧЧ:ММ:СС] Текст фразы

Пример:
[09:00:15 - 09:00:22] Селям алейкум, что будете?
[09:00:23 - 09:00:28] Алейкум селям! Один латте, пожалуйста.

ПРАВИЛА:
1. Каждая строка = одна фраза или реплика
2. НЕ добавляй пометки говорящих (Бариста:, Клиент: и т.д.) — только чистый текст
3. Если ничего не слышно или только шум — пропускай этот участок
4. Крымскотатарские слова пиши кириллицей: Селям, Алейкум, Сагъ ол, Мерхаба
5. Пиши ВСЁ, что слышишь — каждую реплику, даже короткую ("Да", "Ага", "Спасибо")
6. Таймкоды должны идти последовательно и не перекрываться"""

    try:
        # Загружаем аудиофайл
        audio_bytes = ogg_path.read_bytes()
        audio_part = types.Part.from_bytes(data=audio_bytes, mime_type="audio/ogg")

        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=[prompt, audio_part],
            config=types.GenerateContentConfig(
                temperature=0.1,
                max_output_tokens=65000,
            ),
        )

        text = response.text.strip() if response.text else None

        if text:
            # Считаем строки с таймкодами
            lines = [l for l in text.split("\n") if re.match(r"\[\d{2}:\d{2}:\d{2}", l)]
            print(f" [OK] {len(lines)} строк")
            return text
        else:
            print(f" [WARN] Пустой ответ")
            if response.candidates:
                for c in response.candidates:
                    if c.finish_reason:
                        print(f"       Причина: {c.finish_reason}")
            return None

    except Exception as e:
        error_str = str(e)
        print(f" [ERR] {error_str[:120]}")

        # Rate limit — ждём и пробуем другим ключом
        if "429" in error_str or "quota" in error_str.lower() or "resource" in error_str.lower():
            print(f"    [WAIT] Rate limit, жду 60 сек...")
            time.sleep(60)
            return transcribe_audio_file(ogg_path, file_start_hour, file_start_min)

        return None


def process_day(date_str: str) -> Path | None:
    """
    Обрабатывает все OGG-файлы за один день.
    Возвращает путь к итоговому canvas-файлу.
    """
    day_dir = AUDIO_BASE / date_str
    if not day_dir.exists():
        print(f"[ERR] Папка не найдена: {day_dir}")
        return None

    # Собираем OGG-файлы
    ogg_files = sorted(day_dir.glob("*.ogg"))
    if not ogg_files:
        print(f"[ERR] Нет OGG-файлов в {day_dir}")
        return None

    # Фильтруем слишком маленькие файлы (< 100KB = пустышки)
    ogg_files = [f for f in ogg_files if f.stat().st_size > 100_000]

    print(f"\n{'='*70}")
    print(f"[DAY] {date_str} | {len(ogg_files)} файлов")
    print(f"{'='*70}")

    # Итоговый canvas
    canvas_lines = []
    canvas_lines.append(f"# Транскрипция Gemini | Ак мечеть | {date_str}")
    canvas_lines.append(f"# Создано: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    canvas_lines.append(f"# Модель: gemini-3.6-flash")
    canvas_lines.append("")

    total_lines = 0
    success_count = 0
    fail_count = 0

    for i, ogg_path in enumerate(ogg_files, 1):
        fname = ogg_path.name
        hour, minute = parse_ogg_start_time(fname)
        size_mb = ogg_path.stat().st_size / 1024 / 1024

        print(f"\n  [{i}/{len(ogg_files)}] {fname} ({size_mb:.1f} MB, начало: {hour:02d}:{minute:02d})")

        # Проверяем — уже транскрибирован?
        hour_output = OUTPUT_DIR / f"{date_str}_{fname.replace('.ogg', '')}_gemini.txt"
        if hour_output.exists() and hour_output.stat().st_size > 1000:
            print(f"    [SKIP] Уже есть ({hour_output.stat().st_size // 1024} KB), пропускаем")
            # Читаем готовый файл и добавляем в canvas
            transcript = hour_output.read_text(encoding="utf-8")
            canvas_lines.append(f"## {fname} (начало: {hour:02d}:{minute:02d})")
            canvas_lines.append("")
            for line in transcript.split("\n"):
                line = line.strip()
                if re.match(r"\[\d{2}:\d{2}:\d{2}\s*-\s*\d{2}:\d{2}:\d{2}\]", line):
                    canvas_lines.append(line)
                    total_lines += 1
            canvas_lines.append("")
            success_count += 1
            continue

        # Транскрибируем
        transcript = transcribe_audio_file(ogg_path, hour, minute)

        if transcript:
            # Добавляем секцию в canvas
            canvas_lines.append(f"## {fname} (начало: {hour:02d}:{minute:02d})")
            canvas_lines.append("")

            # Парсим строки с таймкодами
            for line in transcript.split("\n"):
                line = line.strip()
                if re.match(r"\[\d{2}:\d{2}:\d{2}\s*-\s*\d{2}:\d{2}:\d{2}\]", line):
                    canvas_lines.append(line)
                    total_lines += 1

            canvas_lines.append("")
            success_count += 1

            # Сохраняем промежуточный результат каждого часа отдельно
            hour_output = OUTPUT_DIR / f"{date_str}_{fname.replace('.ogg', '')}_gemini.txt"
            hour_output.write_text(transcript, encoding="utf-8")
        else:
            canvas_lines.append(f"## {fname} (начало: {hour:02d}:{minute:02d})")
            canvas_lines.append("(транскрипция не получена)")
            canvas_lines.append("")
            fail_count += 1

        # Пауза между запросами (rate limit protection)
        if i < len(ogg_files):
            wait = 5 if len(API_KEYS) >= 3 else 15
            print(f"    [WAIT] Пауза {wait} сек...")
            time.sleep(wait)

    # Сохраняем итоговый canvas
    canvas_path = OUTPUT_DIR / f"daily_canvas_{date_str}_gemini.txt"
    canvas_path.write_text("\n".join(canvas_lines), encoding="utf-8")

    print(f"\n{'='*70}")
    print(f"  [RESULT] Итог за {date_str}:")
    print(f"     [OK]   Успешно: {success_count}/{len(ogg_files)} файлов")
    print(f"     [ERR]  Ошибки:  {fail_count}/{len(ogg_files)} файлов")
    print(f"     [LINE] Строк с таймкодами: {total_lines}")
    print(f"     [SAVE] Canvas: {canvas_path}")
    print(f"{'='*70}")

    return canvas_path


def main():
    parser = argparse.ArgumentParser(description="Gemini Transcriber")
    parser.add_argument(
        "--dates",
        nargs="+",
        required=True,
        help="Даты для обработки (формат: YYYY-MM-DD)",
    )
    args = parser.parse_args()

    print(f"[START] Gemini Transcriber")
    print(f"   Даты: {', '.join(args.dates)}")
    print(f"   Ключей: {len(API_KEYS)}")
    print(f"   Выход: {OUTPUT_DIR}")

    results = []
    for date_str in args.dates:
        canvas_path = process_day(date_str)
        if canvas_path:
            results.append((date_str, canvas_path))

    # Итоговая сводка
    print(f"\n{'='*70}")
    print(f"[DONE] ГОТОВО!")
    print(f"{'='*70}")
    for date_str, path in results:
        print(f"  {date_str} -> {path}")
    print(f"\nФайлы сохранены в: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
