"""
Замер реального расхода токенов на один OGG файл.
Берёт первый попавшийся файл, отправляет, выводит точные цифры из API.
"""
import os, sys
from pathlib import Path
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
load_dotenv(Path(__file__).parent / ".env")

from google import genai
from google.genai import types

# Берём живой ключ
key = os.environ.get("GEMINI_KEY_4")
client = genai.Client(api_key=key)

# Берём один файл
test_file = Path(r"E:\talk\АУДИОЗАПИСИ\Ак мечеть\2026-06-21\09-00-21-06-2026.ogg")
print(f"Файл: {test_file.name}")
print(f"Размер: {test_file.stat().st_size / 1024 / 1024:.1f} MB")

audio_bytes = test_file.read_bytes()
audio_part = types.Part.from_bytes(data=audio_bytes, mime_type="audio/ogg")

prompt = "Транскрибируй эту аудиозапись в текст с таймкодами."

response = client.models.generate_content(
    model="gemini-3.6-flash",
    contents=[prompt, audio_part],
    config=types.GenerateContentConfig(
        temperature=0.1,
        max_output_tokens=65000,
    ),
)

# Реальные данные из API
meta = response.usage_metadata
print(f"\n=== РЕАЛЬНЫЙ РАСХОД ТОКЕНОВ ===")
print(f"Input tokens (аудио + промпт): {meta.prompt_token_count:,}")
print(f"Output tokens (транскрипция):  {meta.candidates_token_count:,}")
print(f"TOTAL:                         {meta.total_token_count:,}")

# Стоимость по тарифу 3.6 Flash
input_cost  = meta.prompt_token_count     / 1_000_000 * 1.50
output_cost = meta.candidates_token_count / 1_000_000 * 7.50
total_cost  = input_cost + output_cost

print(f"\n=== СТОИМОСТЬ ОДНОГО ФАЙЛА ($1.5/M input, $7.5/M output) ===")
print(f"Input:  ${input_cost:.4f}")
print(f"Output: ${output_cost:.4f}")
print(f"Итого:  ${total_cost:.4f}")

# Экстраполяция на день (14 файлов)
print(f"\n=== ЭКСТРАПОЛЯЦИЯ НА 1 ДЕНЬ (14 файлов) ===")
print(f"Input tokens:  {meta.prompt_token_count * 14:,}")
print(f"Output tokens: {meta.candidates_token_count * 14:,}")
print(f"Стоимость:     ${total_cost * 14:.2f}")
print(f"\nМесяц (22 дня): ${total_cost * 14 * 22:.2f}")
