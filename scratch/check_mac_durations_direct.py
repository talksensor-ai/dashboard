import subprocess

mac_script = """
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
"""

# Write local script to run
with open("e:\\talk\\scratch\\mac_durations_script.py", "w", encoding="utf-8") as f:
    f.write(mac_script)

try:
    # Run the script by redirecting stdin of ssh python3
    cmd = "ssh ai@100.123.93.21 \"python3\" < e:\\talk\\scratch\\mac_durations_script.py"
    out = subprocess.check_output(cmd, shell=True).decode("utf-8")
    print(out)
except Exception as e:
    print("Error:", e)
