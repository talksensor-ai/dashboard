"""Fix: restart test_day_runner using the correct venv python."""
import paramiko, os, time
from dotenv import load_dotenv
load_dotenv("e:/talk/.env")

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("81.29.139.211", username="root", password=os.environ["SERVER_PASS"])

def run(cmd, timeout=120):
    print(f"$ {cmd}")
    _, o, e = c.exec_command(cmd, timeout=timeout)
    out = o.read().decode()
    err = e.read().decode()
    if out.strip(): print(out.strip())
    if err.strip(): print(f"STDERR: {err.strip()[-300:]}")
    return out

# 1. Verify gigaam is importable from venv
print("=== Step 1: Verify GigaAM in venv ===")
run("/root/talk/.venv/bin/python3 -c 'import gigaam; print(\"GigaAM OK\")'")

# 2. Kill old screen
print("\n=== Step 2: Kill old runner ===")
run("screen -S testday -X quit 2>/dev/null; sleep 1")
run("screen -ls 2>&1")

# 3. Clean up failed file state so it reprocesses
print("\n=== Step 3: Reset log for reprocessing ===")
run("rm -f /root/talk/2026-04-24_09-00-24-04-2026_transcript.txt")
# Reset the log so it reprocesses the file
run("python3 -c \"\nimport json\ntry:\n    with open('/root/talk/test_day_2026-04-24_log.json') as f:\n        d = json.load(f)\n    d['audio_files_processed'] = []\n    d['audio_files_failed'] = []\n    d['errors'] = []\n    with open('/root/talk/test_day_2026-04-24_log.json', 'w') as f:\n        json.dump(d, f)\n    print('Log reset OK')\nexcept: print('No log to reset')\"")

# 4. Start with VENV python
print("\n=== Step 4: Start runner with venv python ===")
run("cd /root/talk && screen -dmS testday -L -Logfile /root/talk/screenlog_testday.log /root/talk/.venv/bin/python3 pipeline/test_day_runner.py")
time.sleep(3)
run("screen -ls 2>&1")

# 5. Verify it's running
run("ps aux | grep test_day | grep -v grep")

# 6. Check initial output
time.sleep(5)
run("tail -20 /root/talk/screenlog_testday.log 2>/dev/null || echo 'no log yet'")

c.close()
print("\nDone! Runner restarted with .venv python.")
