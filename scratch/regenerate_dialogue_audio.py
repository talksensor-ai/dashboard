import os
import glob
import json
import tempfile
import subprocess
import boto3
from dotenv import load_dotenv
from supabase import create_client

env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(env_path)

def get_ogg_files(root_path):
    ogg_files = glob.glob(os.path.join(root_path, "*.ogg"))
    file_shifts = []
    for f in ogg_files:
        basename = os.path.basename(f)
        clean_name = basename
        if '_' in basename:
            clean_name = basename.split('_', 1)[1]
        parts = clean_name.split('-')
        try:
            h = int(parts[0])
            m = int(parts[1])
            shift_s = h * 3600 + m * 60
            file_shifts.append((shift_s, f))
        except:
            continue
    file_shifts.sort(key=lambda x: x[0])
    return file_shifts

def find_audio_segment(global_start, global_end, file_shifts):
    if not file_shifts:
        return None, 0, 0
        
    first_file_shift = file_shifts[0][0]
    # Normalize shifts relative to the start of the first file of the day
    normalized_shifts = [(shift - first_file_shift, fpath) for shift, fpath in file_shifts]
    
    target_file = None
    local_start = global_start
    local_end = global_end
    
    for i in range(len(normalized_shifts)-1, -1, -1):
        shift, fpath = normalized_shifts[i]
        if global_start >= shift:
            target_file = fpath
            local_start = global_start - shift
            local_end = global_end - shift
            break
            
    if not target_file:
        target_file = normalized_shifts[0][1]
        local_start = max(0, global_start - normalized_shifts[0][0])
        local_end = max(1, global_end - normalized_shifts[0][0])
        
    return target_file, local_start, local_end

def cut_audio(local_path, start, end):
    fd, tmp_path = tempfile.mkstemp(suffix=".wav")
    os.close(fd)
    
    ffmpeg_path = "/opt/homebrew/bin/ffmpeg"
    if not os.path.exists(ffmpeg_path):
        ffmpeg_path = "ffmpeg"
        
    ffmpeg_cmd = [
        ffmpeg_path, "-y",
        "-i", local_path,
        "-ss", str(max(0, start - 1.0)),
        "-to", str(end + 1.0),
        "-c:a", "pcm_s16le",
        "-ar", "16000",
        "-ac", "1",
        tmp_path
    ]
    subprocess.run(ffmpeg_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    return tmp_path

def main():
    sb_url = os.environ.get("SUPABASE_URL")
    sb_key = os.environ.get("SUPABASE_SERVICE_ROLE") or os.environ.get("SUPABASE_ANON_KEY")
    if not sb_url or not sb_key:
        print("Missing Supabase credentials!")
        return

    supabase = create_client(sb_url, sb_key)

    r2_access = os.environ.get("R2_ACCESS_KEY")
    r2_secret = os.environ.get("R2_SECRET_KEY")
    r2_account_id = os.environ.get("R2_ACCOUNT_ID")
    r2_bucket = os.environ.get("R2_BUCKET_NAME")
    r2_public_url = os.environ.get("R2_PUBLIC_URL")

    if not all([r2_access, r2_secret, r2_account_id, r2_bucket, r2_public_url]):
        print("Missing R2 credentials!")
        return

    s3 = boto3.client(
        service_name='s3',
        endpoint_url=f'https://{r2_account_id}.r2.cloudflarestorage.com',
        aws_access_key_id=r2_access,
        aws_secret_access_key=r2_secret,
        region_name='auto'
    )

    # Fetch dialogues sorted by created_at
    res = supabase.table("dialogs").select("*").execute()
    dialogs = res.data

    print(f"Loaded {len(dialogs)} dialogs to process.")
    
    root_audio_dir = "/Users/ai/talk"

    for d in dialogs:
        dialog_id = d["id"]
        created_at = d["created_at"]
        date_str = created_at[:10]  # YYYY-MM-DD
        
        transcript = d.get("transcript", [])
        if not transcript:
            continue
            
        starts = [t.get("start") for t in transcript if t.get("start") is not None]
        ends = [t.get("end") for t in transcript if t.get("end") is not None]
        if not starts or not ends:
            continue
            
        global_start = min(starts)
        global_end = max(ends)
        
        # Get file shifts for this specific day
        # For 2026-05-21, ogg files are named e.g., 2026-05-21_08-00-21-05-2026.ogg
        # We can look for .ogg files in the directory
        file_shifts = get_ogg_files(root_audio_dir)
        # Filter files for the specific date
        day_shifts = [(shift, fpath) for shift, fpath in file_shifts if date_str in os.path.basename(fpath)]
        
        if not day_shifts:
            # Fallback to all files if date-specific files are not found
            day_shifts = file_shifts
            
        if not day_shifts:
            print(f"No audio files found for date {date_str}")
            continue

        target_file, local_start, local_end = find_audio_segment(global_start, global_end, day_shifts)
        if not target_file:
            print(f"Could not find segment for dialogue {dialog_id}")
            continue

        print(f"Dialogue {dialog_id} ({date_str}, {global_start}-{global_end}s):")
        print(f"  Target File: {os.path.basename(target_file)}")
        print(f"  Local Offset: {local_start:.1f} - {local_end:.1f}s")
        
        try:
            # Cut audio segment
            audio_segment_path = cut_audio(target_file, local_start, local_end)
            file_name = os.path.basename(audio_segment_path)
            
            # Fetch shop name
            shop_res = supabase.table("shops").select("name").eq("id", d["shop_id"]).execute()
            shop_name = "unknown"
            if shop_res.data:
                shop_name = shop_res.data[0]["name"]
                
            safe_shop = (shop_name or "unknown").replace(" ", "-").lower()
            r2_key = f"{safe_shop}/{date_str}/{file_name}"
            
            # Upload to R2
            with open(audio_segment_path, "rb") as f:
                s3.upload_fileobj(f, r2_bucket, r2_key, ExtraArgs={"ContentType": "audio/wav"})
                
            public_audio_url = f"{r2_public_url.rstrip('/')}/{r2_key}"
            
            # Update Supabase row
            supabase.table("dialogs").update({
                "audio_url": public_audio_url,
                "original_audio_file": file_name
            }).eq("id", dialog_id).execute()
            
            print(f"  Updated ID {dialog_id} audio_url -> {public_audio_url}")
            os.remove(audio_segment_path)
            
        except Exception as e:
            print(f"  Error processing dialogue {dialog_id}: {e}")

if __name__ == "__main__":
    main()
