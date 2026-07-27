import os
import re

with open('e:\\talk\\run_iterator_21may_mac_resume.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace hardcoded vars with argparse
argparse_code = '''
import argparse

# Parse arguments FIRST so we can use DATE_FOLDER
parser = argparse.ArgumentParser(description='Audio Audit Pipeline')
parser.add_argument('--date', required=True, help='Date in YYYY-MM-DD format (e.g., 2026-05-21)')
parser.add_argument('--limit', type=int, default=1, help='Max dialogues to process')
# parse_known_args in case other args are passed implicitly
args, _ = parser.parse_known_args()

DATE_FOLDER = args.date
SHOP_ID = 8
SHOP_NAME = "Ак-Мечеть"
CANVAS_FILE = f"/Users/ai/talk/daily_canvas_{DATE_FOLDER}_cumulative.txt"
RESULTS_FILE = f"/Users/ai/talk/pipeline/results_{DATE_FOLDER}.json"
OGG_DIR = "/Users/ai/talk"

MAX_DIALOGUES = args.limit
WINDOW_SIZE = 10000
WINDOW_EXPAND = 5000
'''

# The original code has lines from DATE_FOLDER = "2026-05-21" to WINDOW_EXPAND = 5000
# We use regex to replace that block
content = re.sub(
    r'DATE_FOLDER = "2026-05-21".*?WINDOW_EXPAND = 5000\s*#[^\n]*',
    argparse_code.strip(),
    content,
    flags=re.DOTALL
)

# Replace models
content = content.replace('"deepseek-chat"', '"deepseek-v4-pro"')
content = content.replace('"deepseek-reasoner"', '"deepseek-v4-pro"')

with open('e:\\talk\\pipeline\\main.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('main.py created successfully.')
