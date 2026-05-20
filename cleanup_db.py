"""Clean up database: remove duplicates and old test data."""
import os
from dotenv import load_dotenv
from supabase import create_client
load_dotenv("e:/talk/.env")

url = os.environ["SUPABASE_URL"]
key = os.environ["SUPABASE_SERVICE_ROLE"]
sb = create_client(url, key)

# 1. Get all records for shop_id=8 
res = sb.table("dialogs").select("id, shop_id, created_at, dialog_index").eq("shop_id", 8).order("created_at").execute()
print(f"Total records for shop_id=8: {len(res.data)}")

# 2. Identify records to keep (April 23, one per dialog_index)
keep_ids = set()
april23 = [r for r in res.data if r["created_at"].startswith("2026-04-23")]
print(f"\nApril 23 records: {len(april23)}")

# Keep only one record per dialog_index (the one with highest ID = latest)
by_idx = {}
for r in april23:
    idx = r["dialog_index"]
    if idx not in by_idx or r["id"] > by_idx[idx]["id"]:
        by_idx[idx] = r
for r in by_idx.values():
    keep_ids.add(r["id"])
    print(f"  KEEP: id={r['id']} idx={r['dialog_index']} date={r['created_at']}")

# 3. Identify records to delete (everything else for shop_id=8)
delete_ids = [r["id"] for r in res.data if r["id"] not in keep_ids]
print(f"\nRecords to DELETE: {len(delete_ids)}")
for did in delete_ids:
    r = next(x for x in res.data if x["id"] == did)
    print(f"  DELETE: id={did} idx={r['dialog_index']} date={r['created_at']}")

# 4. Delete
if delete_ids:
    confirm = input(f"\nDelete {len(delete_ids)} records? (y/n): ")
    if confirm.lower() == 'y':
        for did in delete_ids:
            sb.table("dialogs").delete().eq("id", did).execute()
        print(f"Deleted {len(delete_ids)} records!")
    else:
        print("Cancelled.")
else:
    print("Nothing to delete.")

# Verify
res2 = sb.table("dialogs").select("id, created_at, dialog_index").eq("shop_id", 8).order("created_at").execute()
print(f"\nRemaining records: {len(res2.data)}")
for r in res2.data:
    print(f"  id={r['id']} idx={r['dialog_index']} date={r['created_at']}")
