import re

with open('src/app/page.tsx', 'r', encoding='utf-8') as f:
    code = f.read()

bad_line = '{agentIsBusy.active_task.substring(0, 20)}...'
good_line = '{(agentIsBusy.active_task || "Обработка аудио...").substring(0, 20)}...'

code = code.replace(bad_line, good_line)

with open('src/app/page.tsx', 'w', encoding='utf-8') as f:
    f.write(code)

print("done")
