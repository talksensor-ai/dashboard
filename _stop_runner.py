"""Stop the broken test_day_runner and check its current status."""
import paramiko
import time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('81.29.139.211', username='root', password='nIyjYRinAVKAPL23bk6f')

# Kill the screen session
print("Stopping test_day_runner...")
_, out, _ = ssh.exec_command('screen -S testday -X quit 2>/dev/null; echo "Screen killed"')
time.sleep(2)
print(out.read().decode('utf-8', 'replace'))

# Check if any python still running
_, out, _ = ssh.exec_command('ps aux | grep test_day | grep -v grep')
time.sleep(2)
result = out.read().decode('utf-8', 'replace')
if result.strip():
    print(f"Still running: {result}")
    _, out, _ = ssh.exec_command('pkill -f test_day_runner')
    time.sleep(1)
    print("Force killed")
else:
    print("No test_day_runner process found (already stopped)")

# Check what it did so far
print("\nChecking what was processed...")
_, out, _ = ssh.exec_command('ls -la /root/talk/daily_canvas_2026-04-2*.txt /root/talk/pipeline/daily_canvas_2026-04-2*.txt 2>/dev/null')
time.sleep(2)
print(out.read().decode('utf-8', 'replace'))

ssh.close()
print("Done! Runner is stopped.")
