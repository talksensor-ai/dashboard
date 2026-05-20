"""Full server inspection script."""
import paramiko, os
from dotenv import load_dotenv
load_dotenv("e:/talk/.env")

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(os.environ["SERVER_IP"], username=os.environ["SERVER_USER"],
            password=os.environ["SERVER_PASS"], timeout=30, banner_timeout=200)

commands = [
    ("=== DISK USAGE ===", "df -h"),
    ("=== TOTAL /root SIZE ===", "du -sh /root/"),
    ("=== /root TOP-LEVEL ===", "ls -la /root/"),
    ("=== /root/talk SIZE BREAKDOWN ===", "du -sh /root/talk/*/ 2>/dev/null; echo '---'; du -sh /root/talk/"),
    ("=== /root/talk FILE COUNT (top level) ===", "find /root/talk -maxdepth 1 -type f | wc -l"),
    ("=== /root/talk TOTAL FILE COUNT (recursive) ===", "find /root/talk -type f | wc -l"),
    ("=== AUDIO FILES COUNT + SIZE ===", r"find /root/talk \( -name '*.ogg' -o -name '*.wav' \) -exec du -ch {} + | tail -1"),
    ("=== AUDIO FILES LIST ===", r"find /root/talk \( -name '*.ogg' -o -name '*.wav' \) -exec ls -lh {} \;"),
    ("=== OTHER DIRS IN /root ===", "ls -d /root/*/ 2>/dev/null"),
    ("=== OTHER DIR SIZES ===", "du -sh /root/*/ 2>/dev/null"),
    ("=== RUNNING PROCESSES ===", "ps aux --sort=-%mem | head -20"),
    ("=== CRONTAB ===", "crontab -l 2>/dev/null || echo No crontab"),
    ("=== SYSTEMD SERVICES (running) ===", "systemctl list-units --type=service --state=running 2>/dev/null | head -30"),
    ("=== PYTHON VERSION ===", "python3 --version; which python3"),
    ("=== VENV PACKAGES ===", "/root/talk/.venv/bin/pip list 2>/dev/null || echo No venv"),
    ("=== OS INFO ===", "cat /etc/os-release | head -5"),
    ("=== RAM ===", "free -h"),
    ("=== CPU ===", "nproc; cat /proc/cpuinfo | grep 'model name' | head -1"),
    ("=== GPU ===", "nvidia-smi 2>/dev/null || echo No GPU"),
    ("=== SCREEN/TMUX SESSIONS ===", "screen -ls 2>/dev/null; tmux list-sessions 2>/dev/null || echo None"),
    ("=== DOCKER ===", "docker ps 2>/dev/null || echo No docker"),
    ("=== LISTENING PORTS ===", "ss -tlnp | head -20"),
]

for title, cmd in commands:
    print(title)
    _, stdout, stderr = ssh.exec_command(cmd)
    out = stdout.read().decode()
    err = stderr.read().decode()
    if out:
        print(out)
    if err and "No such file" not in err:
        print("STDERR:", err)
    print()

ssh.close()
print("=== DONE ===")
