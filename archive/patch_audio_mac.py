import os
import json
import logging
from supabase import create_client
import boto3
import tempfile
import sys
from emotion_analyzer import analyze_emotion_and_tag

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

def patch_audio():
    # Supabase setup
    sb_url = os.environ.get('NEXT_PUBLIC_SUPABASE_URL') or os.environ.get('SUPABASE_URL')
    sb_key = os.environ.get('SUPABASE_SERVICE_ROLE') or os.environ.get('NEXT_PUBLIC_SUPABASE_ANON_KEY')
    if not sb_url or not sb_key:
        logging.error("No Supabase credentials")
        return
        
    sb = create_client(sb_url, sb_key)

    # Cloudflare R2 setup
    r2_account = os.environ.get('R2_ACCOUNT_ID')
    r2_endpoint = f"https://{r2_account}.r2.cloudflarestorage.com" if r2_account else os.environ.get('CLOUDFLARE_R2_ENDPOINT')
    r2_access = os.environ.get('R2_ACCESS_KEY') or os.environ.get('CLOUDFLARE_R2_ACCESS_KEY')
    r2_secret = os.environ.get('R2_SECRET_KEY') or os.environ.get('CLOUDFLARE_R2_SECRET_KEY')
    r2_bucket = os.environ.get('R2_BUCKET_NAME') or os.environ.get('CLOUDFLARE_R2_BUCKET', 'kavabanga-audio')
    
    s3 = boto3.client('s3',
                      endpoint_url=r2_endpoint,
                      aws_access_key_id=r2_access,
                      aws_secret_access_key=r2_secret,
                      region_name='auto')

    res = sb.table('dialogs').select('id, created_at, transcript, clean_text, audio_url').eq('shop_id', 8).execute()
    dialogs = [r for r in res.data if '2026-05-21' in r['created_at']]
    
    logging.info(f"Found {len(dialogs)} dialogs for May 21st.")
    
    for d in dialogs:
        # Check if we need to patch
        needs_patch = False
        if not d.get('audio_url') or 'tmp_xhv6iyj.wav' in d.get('audio_url', ''):
            needs_patch = True
            
        if not needs_patch:
            logging.info(f"Dialog {d['id']} already has valid audio.")
            continue
            
        start_time = d['transcript'][0].get('start') if d.get('transcript') else None
        end_time = d['transcript'][-1].get('end') if d.get('transcript') else None
        
        if start_time is None or end_time is None:
            logging.warning(f"Dialog {d['id']} missing timestamps.")
            continue
            
        logging.info(f"Patching dialog {d['id']} (start={start_time}, end={end_time})")
        
        tag, is_conflict, audio_path = analyze_emotion_and_tag(start_time, end_time, "2026-05-21", "/Users/ai/talk")
        
        if not audio_path or not os.path.exists(audio_path):
            logging.error(f"Failed to generate audio for dialog {d['id']}")
            continue
            
        # Upload to R2
        object_name = f"ак-мечеть/2026-05-21/{os.path.basename(audio_path)}"
        
        try:
            s3.upload_file(
                audio_path,
                r2_bucket,
                object_name,
                ExtraArgs={'ContentType': 'audio/wav'}
            )
            public_url = f"https://pub-00c77c70f2f54813abf1578a369f0139.r2.dev/{object_name}"
            logging.info(f"Uploaded to {public_url}")
        except Exception as e:
            logging.error(f"Failed to upload to R2: {e}")
            continue
            
        # Update text if needed
        clean_text = d.get('clean_text', '')
        if "[ЭМОЦИИ: ОШИБКА]" in clean_text:
            clean_text = clean_text.replace("[ЭМОЦИИ: ОШИБКА]", tag)
            
        # Update Supabase
        update_data = {
            'audio_url': public_url,
            'clean_text': clean_text
        }
        
        sb.table('dialogs').update(update_data).eq('id', d['id']).execute()
        logging.info(f"Patched dialog {d['id']} successfully!")

if __name__ == '__main__':
    patch_audio()
