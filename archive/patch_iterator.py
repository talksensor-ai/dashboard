import re

file_path = '/Users/ai/talk/pipeline/run_iterator_21may.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix push_report_to_supabase call
old_push = '''        audio_path_to_push = d.get('audio_path', '')
        push_report_to_supabase(
            json_path=tmp_path,
            shop_id=SHOP_ID,
            audio_path=audio_path_to_push,
            date_folder=date_folder,
            shop_name=SHOP_NAME
        )'''

new_push = '''        audio_path_to_push = evaluated.get('audio_path', '')
        push_report_to_supabase(
            json_path=tmp_path,
            shop_id=SHOP_ID,
            audio_path=audio_path_to_push,
            date_folder=date_folder,
            shop_name=SHOP_NAME
        )'''

if old_push in content:
    content = content.replace(old_push, new_push)
    print("Replaced push_report_to_supabase call")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Patch applied successfully!")
