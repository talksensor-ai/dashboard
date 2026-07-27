import json

def inspect():
    with open('/Users/ai/talk/pipeline/results_2026-05-21.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    results = data.get('results', [])
    print(f"Total results in results_2026-05-21.json: {len(results)}")
    for r in results[:10]:
        idx = r.get('idx')
        eval_data = r.get('evaluation', {})
        transcript = eval_data.get('transcript', [])
        starts = [t.get('start') for t in transcript if t.get('start') is not None]
        ends = [t.get('end') for t in transcript if t.get('end') is not None]
        min_start = min(starts) if starts else None
        max_end = max(ends) if ends else None
        print(f"Dialogue #{idx}: min_start={min_start}, max_end={max_end}, audio_path={eval_data.get('audio_path')}")

if __name__ == "__main__":
    inspect()
