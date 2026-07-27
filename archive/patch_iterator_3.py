import re

file_path = '/Users/ai/talk/pipeline/run_iterator_21may.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix qa_queue.put to preserve audio_path
old_put = '''            qa_queue.put({"idx": dialog_idx, "text": final_text})'''

new_put = '''            qa_queue.put({"idx": dialog_idx, "text": final_text, "audio_path": cut_audio_path})'''

if old_put in content:
    content = content.replace(old_put, new_put)
    print("Replaced qa_queue.put block")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Patch applied successfully!")
