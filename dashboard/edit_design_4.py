import re

file_path = r"e:\talk\dashboard\src\app\page.tsx"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Remove Window import
content = content.replace('import { Window } from "@pikoloo/darwin-ui";\n', '')

# Replace card backgrounds to clean Apple web style
replacements = {
    # Fix cards
    r'bg-card text-card-foreground border border-border shadow-sm rounded-2xl': 'bg-white dark:bg-[#1c1c1e] text-[#1d1d1f] dark:text-[#f5f5f7] rounded-3xl shadow-[0_4px_24px_rgba(0,0,0,0.04)] dark:shadow-none border border-black/5 dark:border-white/5',
    r'bg-card text-card-foreground border border-border rounded-2xl shadow-sm': 'bg-white dark:bg-[#1c1c1e] text-[#1d1d1f] dark:text-[#f5f5f7] rounded-3xl shadow-[0_4px_24px_rgba(0,0,0,0.04)] dark:shadow-none border border-black/5 dark:border-white/5',
    r'bg-card border-transparent shadow-xl': 'bg-white dark:bg-[#2c2c2e] shadow-[0_8px_30px_rgba(0,0,0,0.12)] border-none',
    
    # Fix muted panels
    r'bg-muted text-muted-foreground border border-border rounded-xl': 'bg-[#f5f5f7] dark:bg-[#2c2c2e] text-[#86868b] dark:text-[#98989d] rounded-2xl border-none',
    r'bg-muted': 'bg-[#f5f5f7] dark:bg-[#2c2c2e]',
    r'text-muted-foreground': 'text-[#86868b] dark:text-[#98989d]',
    r'text-foreground': 'text-[#1d1d1f] dark:text-[#f5f5f7]',
    r'border-border': 'border-black/5 dark:border-white/5',
    
    # Primary touches
    r'text-primary': 'text-[#0071e3]',
    r'bg-primary': 'bg-[#0071e3]',
    r'text-primary-foreground': 'text-white',
    
    # Specific elements
    r'rounded-2xl': 'rounded-[20px]',
    r'rounded-xl': 'rounded-[16px]',
    r'rounded-lg': 'rounded-[12px]',
    
    # Clean the border on header
    r'border-b border-black/5 dark:border-white/5 pb-10 relative': 'pb-10 relative'
}

for old, new in replacements.items():
    content = content.replace(old, new)

# Fix any leftover string literals that shouldn't be matched exactly like that, but this is simple enough.

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Apple Web Style applied successfully.")
