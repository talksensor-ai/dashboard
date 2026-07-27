import subprocess

try:
    cmd = ["ssh", "ai@100.123.93.21", "cat /Users/ai/talk/pipeline/run_21.log"]
    log_content = subprocess.check_output(cmd).decode("utf-8", errors="ignore")
    lines = log_content.split("\n")
    
    out_lines = []
    for line in lines:
        if "supabase" in line.lower() or "ошибка" in line.lower() or "error" in line.lower() or "timeout" in line.lower() or "disconnect" in line.lower():
            out_lines.append(line)
            
    with open("e:\\talk\\scratch\\supabase_logs.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(out_lines))
        
    print(f"Wrote {len(out_lines)} lines to supabase_logs.txt")
except Exception as e:
    print("Error:", e)
