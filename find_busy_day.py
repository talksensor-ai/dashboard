import os
from dotenv import load_dotenv
import yadisk

load_dotenv('e:/talk/.env')
y = yadisk.YaDisk(token=os.environ['YANDEX_TOKEN'])

# Decoded 'Ак мечеть'
folder_name = bytes.fromhex('d090d0ba20d0bcd0b5d187d0b5d182d18c').decode('utf-8')
print(f"Scanning folder: {folder_name}")

stats = {}
try:
    dirs = [i.name for i in list(y.listdir('/' + folder_name)) if i.type == 'dir']
    for d in dirs:
        try:
            files = [f.name for f in list(y.listdir(f'/{folder_name}/{d}')) if f.name.endswith('.ogg')]
            stats[d] = len(files)
            print(f"  {d}: {len(files)} files")
        except:
            pass
    
    if stats:
        max_day = max(stats, key=stats.get)
        print(f"\nRESULT: {max_day} has {stats[max_day]} files.")
    else:
        print("No folders with .ogg files found.")
except Exception as e:
    print(f"Error: {e}")
