import datetime
import os
import json
from supabase import create_client

url = os.environ.get('NEXT_PUBLIC_SUPABASE_URL') or 'https://itllqtmuvktatmpalzxo.supabase.co'
key = os.environ.get('SUPABASE_SERVICE_ROLE') or os.environ.get('NEXT_PUBLIC_SUPABASE_ANON_KEY')
supabase = create_client(url, key)

res = supabase.table('agent_telemetry').upsert({
    'agent_name': 'mac_mini_telemetry',
    'status': 'ONLINE',
    'updated_at': datetime.datetime.now(datetime.timezone.utc).isoformat()
}).execute()
print(res.data)
