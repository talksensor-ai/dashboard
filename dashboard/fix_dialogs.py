import os

file_path = r"e:\talk\dashboard\src\app\page.tsx"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace("dayDialogs.length", "filteredDialogs.length")
content = content.replace("dayDialogs.filter", "filteredDialogs.filter")
content = content.replace("dayDialogs.map", "filteredDialogs.map")

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Fixed dayDialogs.")
