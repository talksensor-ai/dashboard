import os
from dotenv import load_dotenv
from supabase import create_client
load_dotenv("e:/talk/.env")

url = os.environ["SUPABASE_URL"]
key = os.environ["SUPABASE_SERVICE_ROLE"]
sb = create_client(url, key)

# Get all records for shop_id=8
res = sb.table("dialogs").select("id, shop_id, created_at, score, dialog_index").eq("shop_id", 8).order("created_at", desc=True).limit(30).execute()
print(f"Records for shop_id=8 (last 30):")
for r in res.data:
    print(f"  id={r['id']} | date={r['created_at']} | score={r['score']} | idx={r['dialog_index']}")
print(f"\nTotal returned: {len(res.data)}")

# Also check ALL shop_ids to see what's there
res2 = sb.table("dialogs").select("shop_id, created_at").order("created_at", desc=True).limit(10).execute()
print(f"\nLatest 10 records (all shops):")
for r in res2.data:
    print(f"  shop_id={r['shop_id']} | date={r['created_at']}")
