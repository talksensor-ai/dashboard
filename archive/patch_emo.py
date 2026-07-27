import re

content = open('e:/talk/emotion_analyzer_mac.py', 'r', encoding='utf-8').read()

content = content.replace(
    'def get_emotion_score(global_start, global_end, date_folder, root_path="/root/talk/test_compare"):',
    'def get_emotion_score(global_start, global_end, target_audio_file):'
)

content = content.replace(
    'def analyze_emotion_and_tag(global_start, global_end, date_folder, root_path):',
    'def analyze_emotion_and_tag(global_start, global_end, target_audio_file):'
)

content = content.replace(
    'probs, audio_path = get_emotion_score(global_start, global_end, date_folder, root_path)',
    'probs, audio_path = get_emotion_score(global_start, global_end, target_audio_file)'
)

new_logic = """
    target_file = target_audio_file
    local_start = global_start
    local_end = global_end
    
    print(f"[EMO] Локальный {local_start}-{local_end} в {target_file}")
    
    try:
"""

content = re.sub(r'    import gigaam.*?try:', new_logic, content, flags=re.DOTALL)

with open('e:/talk/emotion_analyzer_mac.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Patched successfully.')
