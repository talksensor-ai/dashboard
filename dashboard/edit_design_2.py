import re
import os

file_path = r"e:\talk\dashboard\src\app\page.tsx"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Replace hardcoded backgrounds and texts with semantic equivalents
replacements = {
    r'bg-zinc-100 dark:bg-zinc-900': 'bg-muted',
    r'bg-zinc-200 dark:bg-zinc-800': 'bg-muted hover:bg-muted/80',
    r'bg-white dark:bg-zinc-900': 'bg-card',
    r'bg-white dark:bg-\[#0c0d12\]': 'bg-card',
    r'dark:bg-\[#0c0d12\]': 'dark:bg-card',
    r'bg-zinc-100 dark:bg-\[#0c0d12\]': 'bg-muted',
    r'text-zinc-500 dark:text-zinc-400': 'text-muted-foreground',
    r'text-zinc-600 dark:text-zinc-400': 'text-muted-foreground',
    r'text-zinc-600 dark:text-zinc-500': 'text-muted-foreground',
    r'text-zinc-400 dark:text-zinc-500': 'text-muted-foreground',
    r'text-zinc-500': 'text-muted-foreground',
    r'text-zinc-600': 'text-muted-foreground',
    r'text-zinc-400': 'text-muted-foreground',
    r'text-zinc-700 dark:text-zinc-300': 'text-foreground',
    r'text-zinc-800 dark:text-white/70': 'text-foreground',
    r'text-zinc-900 dark:text-zinc-300': 'text-foreground',
    r'text-zinc-900 dark:text-zinc-100': 'text-foreground',
    r'text-black dark:text-white': 'text-foreground',
    r'text-white dark:text-black': 'text-primary-foreground',
    r'border-black/5 dark:border-white/5': 'border-border',
    r'border-black/5 dark:border-white/10': 'border-border',
    r'border-black/10 dark:border-white/10': 'border-border',
    r'border-black/5': 'border-border',
    r'bg-zinc-900 dark:bg-white': 'bg-primary',
    r'bg-zinc-900 dark:bg-zinc-100': 'bg-primary',
    r'bg-white dark:bg-zinc-800': 'bg-card',
    r'bg-zinc-100 dark:bg-black/20': 'bg-muted',
    r'text-zinc-800 dark:text-white': 'text-foreground',
}

for old, new in replacements.items():
    content = re.sub(old, new, content)

# General sweep for remaining zinc colors (if any)
content = re.sub(r'bg-zinc-[0-9]+ dark:bg-zinc-[0-9]+', 'bg-muted', content)
content = re.sub(r'text-zinc-[0-9]+ dark:text-zinc-[0-9]+', 'text-muted-foreground', content)

# Check the spinner separately
content = re.sub(
    r'border-4 border-zinc-900 border-t-white',
    r'border-4 border-border border-t-primary',
    content
)

# Fix loading screen background
content = re.sub(
    r'<main className="min-h-screen bg-black text-zinc-900 dark:text-white flex items-center justify-center">',
    r'<main className="min-h-screen bg-background text-foreground flex items-center justify-center">',
    content
)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Second design replacement complete.")
