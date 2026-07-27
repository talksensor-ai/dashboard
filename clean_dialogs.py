import os
from dotenv import load_dotenv
from supabase import create_client
load_dotenv('/Users/ai/talk/.env')
url = os.environ.get('SUPABASE_URL') or os.environ.get('NEXT_PUBLIC_SUPABASE_URL')
key = os.environ.get('SUPABASE_SERVICE_ROLE') or os.environ.get('SUPABASE_ANON_KEY')
sb = create_client(url, key)
res = sb.table('dialogs').delete().gte('id', 0).execute()
print('Cleaned dialogs:', len(res.data) if res.data else 0)
