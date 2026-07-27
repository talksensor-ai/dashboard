import json

def run():
    with open('/Users/ai/talk/pipeline/dialogs_dump.json', 'r', encoding='utf-8') as f:
        dialogs = json.load(f)
    if not dialogs:
        print("Empty dump")
        return
    print("Keys of first dialog:")
    print(list(dialogs[0].keys()))
    print("\nSample values for first dialog:")
    for k, v in dialogs[0].items():
        if k not in ['clean_text', 'audit_details']:
            print(f"  {k}: {repr(v)}")
        else:
            print(f"  {k}: {str(v)[:150]}...")

if __name__ == "__main__":
    run()
