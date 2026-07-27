import subprocess

mac_script = """
import glob
import subprocess
import os

files = sorted(glob.glob('/Users/ai/talk/*.ogg'))
for f in files:
    if '2026-05-21' not in os.path.basename(f) and '08-00-19' not in os.path.basename(f):
        continue
    try:
        # Use full path to ffprobe
        cmd = ['/opt/homebrew/bin/ffprobe', '-i', f, '-show_entries', 'format=duration', '-v', 'quiet', '-of', 'csv=p=0']
        dur = subprocess.check_output(cmd).decode().strip()
        print(f"{os.path.basename(f)}: duration = {dur} seconds")
    except Exception as e:
        print(f"Error checking {f}: {e}")
"""

try:
    # Write script to Mac Mini and run it
    write_cmd = ["ssh", "ai@100.123.93.21", "cat > /Users/ai/talk/check_durations_tmp.py"]
    p = subprocess.Popen(write_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = p.communicate(input=mac_script.encode('utf-8'))
    
    run_cmd = ["ssh", "ai@100.123.93.21", "python3 /Users/ai/talk/check_durations_tmp.py"]
    out = subprocess.check_output(run_cmd).decode("utf-8")
    print(out)
    
    # Cleanup Mac script
    subprocess.run(["ssh", "ai@100.123.93.21", "rm /Users/ai/talk/check_durations_tmp.py"])
except Exception as e:
    print("Error:", e)
