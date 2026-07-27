import os
import sys
import yadisk
from dotenv import load_dotenv

load_dotenv()

from pipeline.audio_audit_pipeline import run_gigaam

TOKEN = os.environ.get("YANDEX_TOKEN")
ya = yadisk.YaDisk(token=TOKEN)

remote_path = "/Ак мечеть/2026-05-19/08-00-19-05-2026.ogg"
local_ogg = "08-00-19-05-2026.ogg"
local_txt = "08-00-19-05-2026_transcript.txt"

print(f"Downloading {remote_path} from Yandex Disk...")
try:
    if not os.path.exists(local_ogg):
        ya.download(remote_path, local_ogg)
        print("Download completed.")
    else:
        print("Local OGG already exists.")
except Exception as e:
    print(f"Error downloading: {e}")
    sys.exit(1)

print("Running transcription...")
try:
    run_gigaam(local_ogg, local_txt)
    print(f"Transcription completed! Result saved to {local_txt}")
except Exception as e:
    print(f"Error during transcription: {e}")
    sys.exit(1)

# Print first 30 lines
if os.path.exists(local_txt):
    with open(local_txt, "r", encoding="utf-8") as f:
        lines = f.readlines()
    print("\n--- TRANSCRIPT SNEAK PEEK ---")
    for line in lines[:30]:
        print(line.strip())
