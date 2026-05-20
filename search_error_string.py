import os

search_paths = [
    "/Users/ai/GigaAM",
    "/Users/ai/talk/.venv/lib/python3.12/site-packages"
]

target = "Model type not supported"

for path in search_paths:
    print(f"Searching in {path}...")
    for root, dirs, files in os.walk(path):
        for f in files:
            if f.endswith(".py"):
                full_path = os.path.join(root, f)
                try:
                    with open(full_path, "r", encoding="utf-8", errors="ignore") as file:
                        content = file.read()
                        if target in content:
                            print(f"FOUND in {full_path}")
                except Exception as e:
                    pass
print("Done searching.")
