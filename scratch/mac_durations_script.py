
import glob
import subprocess
import os

files = sorted(glob.glob('/Users/ai/talk/*.ogg'))
for f in files:
    if '2026-05-21' not in os.path.basename(f):
        continue
    try:
        cmd = ['/opt/homebrew/bin/ffprobe', '-i', f, '-show_entries', 'format=duration', '-v', 'quiet', '-of', 'csv=p=0']
        dur = subprocess.check_output(cmd).decode().strip()
        print(f"{os.path.basename(f)}: duration = {dur} seconds")
    except Exception as e:
        print(f"Error checking {f}: {e}")
