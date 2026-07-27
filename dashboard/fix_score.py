import os

file_path = r"e:\talk\dashboard\src\app\page.tsx"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace("d.role_system_score", "d.score")

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Fixed role_system_score.")
