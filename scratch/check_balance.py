import os
import requests
from dotenv import load_dotenv

def main():
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    load_dotenv(env_path)
    
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        print("Error: DEEPSEEK_API_KEY not found in .env!")
        return
        
    url = "https://api.deepseek.com/user/balance"
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            print("=== DeepSeek Account Balance ===")
            print(f"Is available: {data.get('is_available')}")
            for balance in data.get("balance_infos", []):
                print(f"Currency: {balance.get('currency')}")
                print(f"Total Balance: {balance.get('total_balance')}")
                print(f"Granted Balance: {balance.get('granted_balance')}")
                print(f"Topped-up Balance: {balance.get('topped_up_balance')}")
        else:
            print(f"Failed to fetch balance. HTTP Status: {resp.status_code}")
            print(resp.text)
    except Exception as e:
        print(f"Error fetching balance: {e}")

if __name__ == '__main__':
    main()
