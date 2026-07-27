import re
import os

file_path = r"e:\talk\dashboard\src\app\page.tsx"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Main Background and Gradients
content = re.sub(
    r'<main className="min-h-screen bg-zinc-50 dark:bg-\[#050505\] text-zinc-900 dark:text-white pb-32 font-sans selection:bg-black/10 dark:selection:bg-white/20 antialiased overflow-x-hidden transition-colors duration-300">',
    r'<main className="min-h-screen bg-background text-foreground pb-32 font-sans antialiased overflow-x-hidden transition-colors duration-300">',
    content
)

# Remove radial gradients
content = re.sub(
    r'<div className="fixed inset-0 bg-\[radial-gradient.*?></div>\n',
    '',
    content
)

# 2. Cards
content = re.sub(
    r'bg-white dark:bg-zinc-950/40 border border-zinc-200 dark:border-white/5 shadow-sm rounded-2xl backdrop-blur-md',
    r'bg-card text-card-foreground border border-border shadow-sm rounded-2xl',
    content
)
content = re.sub(
    r'bg-white dark:bg-zinc-950 border border-zinc-200 dark:border-white/10 rounded-2xl shadow-sm',
    r'bg-card text-card-foreground border border-border rounded-2xl shadow-sm',
    content
)
content = re.sub(
    r'bg-zinc-50 dark:bg-white/5 border border-zinc-200 dark:border-white/10 rounded-xl',
    r'bg-muted text-muted-foreground border border-border rounded-xl',
    content
)

# 3. Audio Player Capsule
content = re.sub(
    r'bg-zinc-900/90 dark:bg-white/10 backdrop-blur-xl border border-white/10 dark:border-white/20 shadow-2xl rounded-full',
    r'glass-panel border border-border shadow-lg rounded-full',
    content
)

# 4. Progress Bar
content = re.sub(
    r'bg-zinc-700 dark:bg-white/20 rounded-full',
    r'bg-muted rounded-full',
    content
)
content = re.sub(
    r'bg-white dark:bg-white rounded-full relative',
    r'bg-primary rounded-full relative',
    content
)

# 5. Buttons
content = re.sub(
    r'hover:bg-zinc-800 dark:hover:bg-white/20',
    r'hover:bg-muted/80',
    content
)

# 6. Typography adjustments
content = re.sub(
    r'text-zinc-500 dark:text-zinc-400',
    r'text-muted-foreground',
    content
)
content = re.sub(
    r'text-zinc-900 dark:text-white',
    r'text-foreground',
    content
)
content = re.sub(
    r'text-zinc-800 dark:text-zinc-200',
    r'text-foreground',
    content
)

# 7. Chat Bubbles
content = re.sub(
    r'bg-zinc-100 dark:bg-zinc-900 border-zinc-200 dark:border-white/10',
    r'imessage-gray border-transparent',
    content
)
content = re.sub(
    r'bg-blue-50/50 dark:bg-blue-950/30 border-blue-200 dark:border-blue-900/50',
    r'imessage-blue border-transparent',
    content
)
content = re.sub(
    r'border-l-4 border-l-blue-500',
    r'',
    content
)

# 8. Active highlight
content = re.sub(
    r'bg-blue-50 dark:bg-blue-900/20 ring-1 ring-blue-500/30',
    r'ring-2 ring-primary ring-offset-2 ring-offset-background',
    content
)

# 9. Header
content = re.sub(
    r'bg-white/80 dark:bg-zinc-950/80 backdrop-blur-md border-b border-zinc-200 dark:border-white/10',
    r'glass-panel border-b border-border',
    content
)

# 10. Fix hardcoded imports
content = re.sub(
    r'const fontImport = `\n.*?`;\n',
    '',
    content,
    flags=re.DOTALL
)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Design replacement complete.")
