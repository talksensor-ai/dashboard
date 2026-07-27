import json
import re

def inspect():
    # Load results
    with open('/Users/ai/talk/pipeline/results_2026-05-21.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    results = data.get('results', [])
    
    # Load canvas
    with open('/Users/ai/talk/daily_canvas_2026-05-21_cumulative.txt', 'r', encoding='utf-8') as f:
        canvas_lines = f.readlines()
        
    for r in results[:3]:
        idx = r.get('idx')
        eval_data = r.get('evaluation', {})
        transcript = eval_data.get('transcript', [])
        starts = [t.get('start') for t in transcript if t.get('start') is not None]
        ends = [t.get('end') for t in transcript if t.get('end') is not None]
        min_start = min(starts) if starts else None
        max_end = max(ends) if ends else None
        print(f"\n--- Dialogue #{idx} (time: {min_start} - {max_end}) ---")
        print("Transcript lines:")
        for line in transcript[:3]:
            print(f"  [{line.get('start')} - {line.get('end')}] {line.get('speaker')}: {line.get('text')}")
        print("...")
        
        # Find matching lines in canvas
        print("Canvas lines around that time:")
        count = 0
        for line in canvas_lines:
            match = re.match(r'\[(\d+)\s*-\s*(\d+)\]', line.strip())
            if match:
                start = int(match.group(1))
                if min_start is not None and abs(start - min_start) < 60:
                    print("  " + line.strip())
                    count += 1
                    if count > 5:
                        break

if __name__ == "__main__":
    inspect()
