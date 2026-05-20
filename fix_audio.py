"""Upload OGG to R2 and update all dialog records for April 23."""
import os
import boto3
from dotenv import load_dotenv
from supabase import create_client

load_dotenv("e:/talk/.env")

# R2 config
r2_access = os.environ["R2_ACCESS_KEY"]
r2_secret = os.environ["R2_SECRET_KEY"]
r2_account_id = os.environ["R2_ACCOUNT_ID"]
r2_bucket = os.environ["R2_BUCKET_NAME"]
r2_public_url = os.environ["R2_PUBLIC_URL"]

# Audio file
local_ogg = r"e:\talk\21-17-23-04-2026.ogg"
r2_key = "ak-mechet/2026-04-23/21-17-23-04-2026.ogg"

print(f"Uploading {local_ogg} to R2...")
print(f"  Bucket: {r2_bucket}")
print(f"  Key: {r2_key}")
print(f"  Size: {os.path.getsize(local_ogg) / 1024 / 1024:.1f} MB")

# Upload
s3 = boto3.client(
    service_name='s3',
    endpoint_url=f'https://{r2_account_id}.r2.cloudflarestorage.com',
    aws_access_key_id=r2_access,
    aws_secret_access_key=r2_secret,
    region_name='auto'
)

with open(local_ogg, "rb") as f:
    s3.upload_fileobj(f, r2_bucket, r2_key, ExtraArgs={"ContentType": "audio/ogg"})

public_url = f"{r2_public_url.rstrip('/')}/{r2_key}"
print(f"\n[OK] Uploaded! Public URL: {public_url}")

# Update all dialogs for shop_id=8, April 23
sb = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_ROLE"])
res = sb.table("dialogs").select("id").eq("shop_id", 8).execute()

updated = 0
for r in res.data:
    sb.table("dialogs").update({
        "audio_url": public_url,
        "original_audio_file": "21-17-23-04-2026.ogg"
    }).eq("id", r["id"]).execute()
    updated += 1

print(f"[OK] Updated {updated} dialog records with audio_url")
print(f"     URL: {public_url}")
