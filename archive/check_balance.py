import os, requests
from dotenv import load_dotenv
load_dotenv('/Users/ai/talk/.env')
key = os.environ.get('DEEPSEEK_API_KEY')
resp = requests.get('https://api.deepseek.com/user/balance', headers={'Authorization': f'Bearer {key}'})
print(resp.json())
