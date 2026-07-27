import subprocess
import sys

try:
    cmd = ["ssh", "ai@100.123.93.21", "cat /Users/ai/talk/pipeline/run_21.log"]
    out = subprocess.check_output(cmd).decode("utf-8", errors="ignore")
    
    lines = out.split("\n")
    print(f"Total lines in log: {len(lines)}")
    
    print("\n--- Duplicate / Skip / Error messages in Mac log: ---")
    for line in lines:
        if any(w in line.lower() for w in ["пропущен", "дубликат", "ошибка", "error", "fail", "duplicate", "supabase"]):
            # encode to ascii/replace to prevent terminal print errors on Windows
            print(line.encode(sys.stdout.encoding or 'utf-8', errors='replace').decode(sys.stdout.encoding or 'utf-8'))
            
except Exception as e:
    print("Error:", e)
