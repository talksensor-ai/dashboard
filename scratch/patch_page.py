with open('e:\\talk\\dashboard\\src\\app\\page.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

# Add formatAbsoluteTime
absolute_time_func = '''
  const formatAbsoluteTime = (time: number) => {
    if (typeof time !== 'number' || isNaN(time) || !isFinite(time)) return "00:00:00";
    const absoluteSeconds = time + 28800;
    const hours = Math.floor(absoluteSeconds / 3600);
    const mins = Math.floor((absoluteSeconds % 3600) / 60);
    const secs = Math.floor(absoluteSeconds % 60);
    return `${hours.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };
'''
if 'formatAbsoluteTime' not in content:
    content = content.replace('const formatTime = (time: number) => {', absolute_time_func.strip() + '\n\n  const formatTime = (time: number) => {')

# Fix transcript formatting
content = content.replace('{formatTime(line.start)}', '{formatAbsoluteTime(line.start)}')

# Fix the header timestamp (replacing created_at)
old_timestamp = "{new Date(dialog.created_at).toLocaleTimeString('ru-RU', {hour: '2-digit', minute:'2-digit'})}"
new_timestamp = "{dialog.audit_details?.transcript?.[0]?.start !== undefined ? formatAbsoluteTime(dialog.audit_details.transcript[0].start) : new Date(dialog.created_at).toLocaleTimeString('ru-RU', {hour: '2-digit', minute:'2-digit'})}"
content = content.replace(old_timestamp, new_timestamp)

with open('e:\\talk\\dashboard\\src\\app\\page.tsx', 'w', encoding='utf-8') as f:
    f.write(content)
print('Patched page.tsx')
