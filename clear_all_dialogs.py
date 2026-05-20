import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv("e:/talk/.env")

url = os.environ["SUPABASE_URL"]
key = os.environ["SUPABASE_SERVICE_ROLE"]
sb = create_client(url, key)

print("Fetching all dialogs...")
res = sb.table("dialogs").select("id").execute()
dialog_ids = [r["id"] for r in res.data]

print(f"Found {len(dialog_ids)} dialogs. Deleting...")

for chunk in [dialog_ids[i:i + 100] for i in range(0, len(dialog_ids), 100)]:
    # Supabase allows deleting by matching an array of IDs
    if chunk:
        sb.table("dialogs").delete().in_("id", chunk).execute()
        print(f"Deleted a chunk of {len(chunk)} dialogs...")

print("All dialogs deleted successfully! Dashboard is now clean.")

# Also update the app_status so it doesn't show an old processing message
sb.table("app_status").update({"status_message": "Ожидание данных..."}).eq("id", 1).execute()
print("App status reset.")
