with open('e:\\talk\\pipeline\\main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add telemetry thread before the loop
telemetry_code = '''
import threading
import time
def telemetry_loop():
    while True:
        try:
            supabase.table("agent_telemetry").upsert({
                "agent_name": "mac_mini_telemetry",
                "status": "ONLINE",
                "updated_at": "now()"
            }).execute()
        except Exception as e:
            pass
        time.sleep(15)

telemetry_thread = threading.Thread(target=telemetry_loop, daemon=True)
telemetry_thread.start()
'''
if 'telemetry_thread' not in content:
    content = content.replace('if __name__ == "__main__":', 'if __name__ == "__main__":\n' + telemetry_code)

# 2. Add skip-time arg
arg_skip = '''parser.add_argument("--skip-time", type=int, default=0, help="Seconds to skip from start")'''
if 'skip-time' not in content:
    content = content.replace('parser.add_argument("--date"', arg_skip + '\n    parser.add_argument("--date"')

# 3. Change last_second init
content = content.replace('last_second = 0', 'last_second = args.skip_time')

with open('e:\\talk\\pipeline\\main.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Patched main.py')
