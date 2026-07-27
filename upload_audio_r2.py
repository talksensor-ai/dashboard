import os
import boto3
from dotenv import load_dotenv

load_dotenv(os.path.expanduser('~/talk/.env'))

r2_access = os.environ.get('R2_ACCESS_KEY')
r2_secret = os.environ.get('R2_SECRET_KEY')
r2_account_id = os.environ.get('R2_ACCOUNT_ID')
r2_bucket = os.environ.get('R2_BUCKET_NAME')
r2_public_url = os.environ.get('R2_PUBLIC_URL')

print(f'Connecting to R2... {r2_bucket}')

s3 = boto3.client(
    's3',
    endpoint_url=f'https://{r2_account_id}.r2.cloudflarestorage.com',
    aws_access_key_id=r2_access,
    aws_secret_access_key=r2_secret
)

folder = '/Users/ai/talk'
date_folder = '2026-05-21'
shop_name = 'ак-мечеть'

from supabase import create_client
url = os.environ.get('SUPABASE_URL') or os.environ.get('NEXT_PUBLIC_SUPABASE_URL')
key = os.environ.get('SUPABASE_SERVICE_ROLE') or os.environ.get('SUPABASE_ANON_KEY')
sb = create_client(url, key)

import glob
oggs = glob.glob(f'{folder}/{date_folder}*.ogg')
print(f'Found {len(oggs)} OGG files')

for ogg in oggs:
    file_name = os.path.basename(ogg)
    r2_key = f'{shop_name}/{date_folder}/{file_name}'
    print(f'Uploading {file_name} to {r2_key}...')
    with open(ogg, 'rb') as f:
        s3.upload_fileobj(f, r2_bucket, r2_key, ExtraArgs={'ContentType': 'audio/ogg'})
    
    public_audio_url = f"{r2_public_url.rstrip('/')}/{r2_key}"
    print(f'URL: {public_audio_url}')
    
    # Update all dialogues matching this file
    res = sb.table('dialogs').update({'audio_url': public_audio_url}).eq('original_audio_file', file_name).execute()
    print(f'Updated {len(res.data)} dialogues in Supabase')

print('Done!')
