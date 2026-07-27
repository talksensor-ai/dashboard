import json

def inspect():
    with open('/Users/ai/talk/pipeline/results_2026-05-21_raw.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"Total dialogues in results_2026-05-21_raw.json: {len(data)}")
    indices = [d.get('idx') for d in data]
    print(f"Indices: {indices}")

if __name__ == "__main__":
    inspect()
