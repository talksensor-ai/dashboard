import os
import json
import logging
from supabase import create_client
import tempfile
import boto3
import subprocess

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

def process_audio(local_path, start, end):
    try:
        fd, tmp_path = tempfile.mkstemp(suffix=".wav")
        os.close(fd)
        
        ffmpeg_cmd = [
            "/opt/homebrew/bin/ffmpeg", "-y",
            "-i", local_path,
            "-ss", str(start),
            "-to", str(end),
            "-c:a", "pcm_s16le",
            "-ar", "16000",
            "-ac", "1",
            tmp_path
        ]
        
        # fallback to standard ffmpeg if homebrew one doesn't exist
        if not os.path.exists("/opt/homebrew/bin/ffmpeg"):
            ffmpeg_cmd[0] = "ffmpeg"
            
        subprocess.run(ffmpeg_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return tmp_path
    except Exception as e:
        logging.error(f"FFmpeg error: {e}")
        return None

def restore_audio():
    # Supabase credentials
    sb_url = os.environ.get("SUPABASE_URL")
    sb_key = os.environ.get("SUPABASE_SERVICE_ROLE") or os.environ.get("SUPABASE_ANON_KEY")
    if not sb_url or not sb_key:
        logging.error("No SUPABASE_URL or SUPABASE_KEY found.")
        return

    supabase = create_client(sb_url, sb_key)

    # R2 credentials
    r2_access = os.environ.get("R2_ACCESS_KEY")
    r2_secret = os.environ.get("R2_SECRET_KEY")
    r2_account_id = os.environ.get("R2_ACCOUNT_ID")
    r2_bucket = os.environ.get("R2_BUCKET_NAME")
    r2_public_url = os.environ.get("R2_PUBLIC_URL")

    if not all([r2_access, r2_secret, r2_account_id, r2_bucket, r2_public_url]):
        logging.error("Missing R2 credentials in environment.")
        return

    s3 = boto3.client(
        service_name='s3',
        endpoint_url=f'https://{r2_account_id}.r2.cloudflarestorage.com',
        aws_access_key_id=r2_access,
        aws_secret_access_key=r2_secret,
        region_name='auto'
    )

    # Fetch dialogues with null audio_url
    res = supabase.table("dialogs").select("id, original_audio_file, created_at, transcript, shop_id").is_("audio_url", "null").execute()
    dialogs = res.data
    
    if not dialogs:
        logging.info("No dialogues need audio restoration.")
        return

    logging.info(f"Found {len(dialogs)} dialogues needing audio restoration.")

    for d in dialogs:
        dialog_id = d["id"]
        original_audio = d["original_audio_file"]
        transcript = d.get("transcript", [])
        
        if not original_audio or not transcript:
            logging.warning(f"Dialog {dialog_id} missing original_audio or transcript. Skipping.")
            continue
            
        date_str = d["created_at"][:10]  # e.g. 2026-05-21
        
        local_audio_path = os.path.join(os.path.dirname(__file__), original_audio)
        if not os.path.exists(local_audio_path):
            logging.warning(f"Local audio file {local_audio_path} not found for dialog {dialog_id}. Skipping.")
            continue
            
        start_ts = min([t["start"] for t in transcript if "start" in t], default=0)
        end_ts = max([t["end"] for t in transcript if "end" in t], default=0)
        
        if start_ts >= end_ts:
            logging.warning(f"Invalid timestamps {start_ts}-{end_ts} for dialog {dialog_id}. Skipping.")
            continue

        # Add 1 sec padding
        local_start = max(0, start_ts - 1.0)
        local_end = end_ts + 1.0

        try:
            logging.info(f"Cutting audio for dialog {dialog_id}: {local_audio_path} from {local_start} to {local_end}")
            audio_segment_path = process_audio(local_audio_path, local_start, local_end)
            if not audio_segment_path:
                logging.error(f"Failed to cut audio for dialog {dialog_id}")
                continue
                
            file_name = os.path.basename(audio_segment_path)
            
            shop_res = supabase.table("shops").select("name").eq("id", d["shop_id"]).execute()
            shop_name = "unknown"
            if shop_res.data:
                shop_name = shop_res.data[0]["name"]
                
            safe_shop = (shop_name or "unknown").replace(" ", "-").lower()
            r2_key = f"{safe_shop}/{date_str}/{file_name}"
            
            with open(audio_segment_path, "rb") as f:
                s3.upload_fileobj(f, r2_bucket, r2_key, ExtraArgs={"ContentType": "audio/wav"})
                
            public_audio_url = f"{r2_public_url.rstrip('/')}/{r2_key}"
            
            supabase.table("dialogs").update({"audio_url": public_audio_url}).eq("id", dialog_id).execute()
            logging.info(f"Successfully restored audio for dialog {dialog_id} -> {public_audio_url}")
            
            os.remove(audio_segment_path)
            
        except Exception as e:
            logging.error(f"Error restoring audio for dialog {dialog_id}: {e}")

if __name__ == "__main__":
    restore_audio()
