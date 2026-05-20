import os
import sys

# Add pipeline directory to path so we can import our script
sys.path.insert(0, '/root/talk/pipeline')
from emotion_analyzer import analyze_emotion_and_tag

# Test 1: A normal dialog (e.g. Dialogue #1)
# Local timestamps in 19-00-27-04-2026.ogg:
# [2 - 4] "Объёмчик средний, маленький."
# Shift is 19 * 3600 = 68400
# So global is 68402 to 68404. Let's make it wider: 68400 to 68430

print("--- ТЕСТ 1: Обычный диалог заказа (первые 30 секунд файла) ---")
tag1, is_conflict1 = analyze_emotion_and_tag(68400, 68430, "2026-04-27", root_path="/root/talk/test_compare")
print(f"Результат EMO 1: {tag1}")
print(f"Флаг конфликта: {is_conflict1}")

print("\n--- ТЕСТ 2: Диалог про ошибку терминала (таймкоды 1399 - 1421) ---")
# 1399 + 68400 = 69799
# 1421 + 68400 = 69821
tag2, is_conflict2 = analyze_emotion_and_tag(69799, 69821, "2026-04-27", root_path="/root/talk/test_compare")
print(f"Результат EMO 2: {tag2}")
print(f"Флаг конфликта: {is_conflict2}")
