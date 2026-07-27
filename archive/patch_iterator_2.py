import re

file_path = '/Users/ai/talk/pipeline/run_iterator_21may.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix qa_worker to preserve audio_path
old_qa = '''        evaluated = run_qa_single(text, idx)
        
        if evaluated:
            print(f"[QA] Диалог #{idx} оценён!")'''

new_qa = '''        evaluated = run_qa_single(text, idx)
        
        if evaluated:
            evaluated["audio_path"] = item.get("audio_path", "")
            print(f"[QA] Диалог #{idx} оценён!")'''

if old_qa in content:
    content = content.replace(old_qa, new_qa)
    print("Replaced qa_worker block")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Patch applied successfully!")
