import os
from dotenv import load_dotenv
import yadisk
from datetime import datetime

load_dotenv('e:/talk/.env')
y = yadisk.YaDisk(token=os.environ['YANDEX_TOKEN'])

print("Checking Yandex Disk for today's files (2026-05-14)...")

def scan_dir(path):
    try:
        items = list(y.listdir(path))
        for i in items:
            if i.type == 'dir':
                if '2026-05-14' in i.name:
                    print(f"FOUND DATE FOLDER: {path}/{i.name}")
                scan_dir(f"{path}/{i.name}")
            else:
                if i.modified.date() == datetime(2026, 5, 14).date():
                    print(f"RECENT FILE: {path}/{i.name} ({i.modified})")
    except Exception as e:
        pass

scan_dir('/')
