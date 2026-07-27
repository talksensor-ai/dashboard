import subprocess

try:
    cmd = ["ssh", "ai@100.123.93.21", "cat /Users/ai/talk/pipeline/run_21.log"]
    log_content = subprocess.check_output(cmd).decode("utf-8", errors="ignore")
    lines = log_content.split("\n")
    
    for i, line in enumerate(lines):
        if "#39" in line:
            # Print context lines around the match
            start = max(0, i - 2)
            end = min(len(lines), i + 3)
            print(f"--- Context for line {i}: ---")
            for j in range(start, end):
                print(f"{j}: {repr(lines[j])}")
                
except Exception as e:
    print("Error:", e)
