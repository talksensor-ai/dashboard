import os
from dotenv import load_dotenv

load_dotenv('e:/talk/.env')

for key, val in os.environ.items():
    if any(k in key.upper() for k in ['DEEPSEEK', 'GEMINI', 'OPENAI', 'SUPABASE', 'CLOUDFLARE', 'R2']):
        print(f"Key: {key} | Has value: {bool(val)}")
