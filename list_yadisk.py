import os
import yadisk
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.environ.get("YANDEX_TOKEN")
ya = yadisk.YaDisk(token=TOKEN)

folder = "/"
print("Searching for 2026-05-19 across all directories...")
try:
    top_items = [i.name for i in ya.listdir("/") if i.type == 'dir']
    found = []
    for top in top_items:
        path = f"/{top}/2026-05-19"
        if ya.exists(path):
            files = [f.name for f in ya.listdir(path) if f.type == 'file']
            found.append((path, files))
            
    with open("yadisk_folders.txt", "w", encoding="utf-8") as f_out:
        if found:
            for p, files in found:
                f_out.write(f"Found path: {p}\n")
                for f in sorted(files):
                    f_out.write(f"  - {f}\n")
        else:
            f_out.write("No folder '2026-05-19' found in any top-level directory.\n")
    print("Wrote search results to yadisk_folders.txt")
except Exception as e:
    print(f"Error: {e}")
