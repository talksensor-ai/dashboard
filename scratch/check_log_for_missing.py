import subprocess
import sys

missing_indices = [39, 40, 50, 51, 55, 62, 66, 67, 77, 80]

try:
    cmd = ["ssh", "ai@100.123.93.21", "cat /Users/ai/talk/pipeline/run_21.log"]
    log_content = subprocess.check_output(cmd).decode("utf-8", errors="ignore")
    lines = log_content.split("\n")
    
    enc = sys.stdout.encoding or 'utf-8'
    
    for idx in missing_indices:
        print(f"\n=== Log search for dialogue #{idx} ===")
        found = False
        for line in lines:
            if f"#{idx}" in line or f" #{idx} " in line:
                print(line.encode(enc, errors='replace').decode(enc))
                found = True
        if not found:
            print("No log entries found referring to this dialogue index.")
            
except Exception as e:
    print("Error:", e)
