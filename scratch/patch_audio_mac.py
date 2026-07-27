import os
import re
import json
import logging
import tempfile
import torchaudio
import soundfile as sf
import boto3
from dotenv import load_dotenv
from supabase import create_client, Client
import gigaam
import torch
import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

BASE_DIR = "/Users/ai/talk"
ENV_PATH = os.path.join(BASE_DIR, '.env')
load_dotenv(ENV_PATH)

# Supabase init
url = os.environ.get("SUPABASE_URL") or os.environ.get("NEXT_PUBLIC_SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE") or os.environ.get("SUPABASE_ANON_KEY")
supabase: Client = create_client(url, key)

# Cloudflare R2 init
R2_ENDPOINT = os.environ.get("R2_ENDPOINT")
R2_ACCESS_KEY = os.environ.get("R2_ACCESS_KEY")
R2_SECRET_KEY = os.environ.get("R2_SECRET_KEY")
R2_BUCKET = os.environ.get("R2_BUCKET_NAME")

s3_client = boto3.client(
    's3',
    endpoint_url=R2_ENDPOINT,
    aws_access_key_id=R2_ACCESS_KEY,
    aws_secret_access_key=R2_SECRET_KEY,
    region_name='auto'
)

# Load Emo Model
device = "cpu"
logging.info("[EMO] Загрузка GigaAM-Emo...")
emo_model = gigaam.load_model("emo", device=device)

def get_file_and_offset_for_dialog(canvas_lines, target_text):
    """Ищет кусок текста в канвасе и возвращает (имя_файла, сдвиг)."""
    # Упрощаем текст для поиска
    target_clean = re.sub(r'[^а-яА-Я0-9]', '', target_text.lower())[:50]
    
    current_file = None
    current_offset = 0
    
    for line in canvas_lines:
        m = re.match(r'^=== Файл: (.*\.ogg), смещение: (\d+)с', line)
        if m:
            current_file = m.group(1)
            current_offset = int(m.group(2))
            continue
            
        line_clean = re.sub(r'[^а-яА-Я0-9]', '', line.lower())
        if target_clean in line_clean and target_clean != "":
            return current_file, current_offset
            
    return None, 0

def upload_to_r2(local_path, file_name):
    try:
        s3_client.upload_file(
            local_path, 
            R2_BUCKET, 
            file_name,
            ExtraArgs={'ContentType': 'audio/ogg'}
        )
        url = f"{os.environ.get('R2_PUBLIC_URL')}/{file_name}"
        return url
    except Exception as e:
        logging.error(f"R2 upload error: {e}")
        return None

def main():
    date_str = "2026-05-21"
    canvas_path = os.path.join(BASE_DIR, f"daily_canvas_{date_str}_cumulative.txt")
    
    if not os.path.exists(canvas_path):
        logging.error(f"Не найден файл {canvas_path}")
        return
        
    with open(canvas_path, 'r', encoding='utf-8') as f:
        canvas_lines = f.readlines()
        
    # Get base time (08:00)
    base_sec = 8 * 3600
    
    # Fetch all dialogs with pagination to avoid ReadTimeout
    dialogs = []
    page_size = 20
    start_row = 0
    while True:
        res = supabase.table("dialogs").select("id,dialog_index,transcript,audit_details").eq("shop_id", 8).gte("created_at", "2026-05-21T00:00:00Z").lte("created_at", "2026-05-21T23:59:59Z").range(start_row, start_row + page_size - 1).execute()
        chunk = res.data
        if not chunk:
            break
        dialogs.extend(chunk)
        start_row += page_size
        if len(chunk) < page_size:
            break
        
    logging.info(f"Найдено {len(dialogs)} диалогов для патчинга.")
    
    for d in dialogs:
        d_id = d["id"]
        idx = d["dialog_index"]
        transcript = d.get("transcript", [])
        if not transcript:
            continue
            
        global_start = transcript[0]["start"]
        global_end = transcript[-1]["end"]
        
        target_text = transcript[0]["text"]
        
        # Find exactly which file this came from
        target_file, offset = get_file_and_offset_for_dialog(canvas_lines, target_text)
        
        if not target_file:
            # Fallback
            logging.warning(f"ID {d_id} (#{idx}): не найден точный файл, используем fallback.")
            target_file = f"{date_str}_08-56-21-05-2026.ogg" # Just a fallback
            
        # Clean target_file if it misses the date prefix
        if not target_file.startswith(date_str):
            full_path = os.path.join(BASE_DIR, f"{date_str}_{target_file}")
            if not os.path.exists(full_path):
                full_path = os.path.join(BASE_DIR, target_file)
        else:
            full_path = os.path.join(BASE_DIR, target_file)
            
        if not os.path.exists(full_path):
            logging.error(f"Файл {full_path} не существует! Пропуск.")
            continue
            
        local_start = max(0, global_start - offset)
        local_end = max(1, global_end - offset)
        
        logging.info(f"ID {d_id} (#{idx}): {target_file} | local: {local_start}-{local_end}s | global: {global_start}")
        
        # CUT AUDIO
        try:
            waveform, sr = torchaudio.load(full_path)
            start_idx = int(local_start * sr)
            end_idx = int(local_end * sr)
            
            start_idx = max(0, min(start_idx, waveform.shape[1] - 1))
            end_idx = max(start_idx + 1, min(end_idx, waveform.shape[1]))
            
            audio_chunk = waveform[:, start_idx:end_idx]
            
            fd, tmp_path = tempfile.mkstemp(suffix=".wav")
            os.close(fd)
            sf.write(tmp_path, audio_chunk[0].numpy(), sr)
            
            # RUN EMOTION
            probs = emo_model.get_probs(tmp_path)
            angry = probs.get("angry", 0)
            is_conflict = angry > 0.65
            
            emo_str = f"[ЭМОЦИИ: angry={angry:.2f}, neutral={probs.get('neutral',0):.2f}, positive={probs.get('positive',0):.2f}, sad={probs.get('sad',0):.2f}]"
            
            # CONVERT TO OGG & UPLOAD
            fd_ogg, tmp_ogg = tempfile.mkstemp(suffix=".ogg")
            os.close(fd_ogg)
            sf.write(tmp_ogg, audio_chunk[0].numpy(), sr, format='OGG')
            
            r2_filename = f"dialog_shop8_{date_str}_{idx}_patched.ogg"
            new_audio_url = upload_to_r2(tmp_ogg, r2_filename)
            
            os.remove(tmp_path)
            os.remove(tmp_ogg)
            
            # CALCULATE REAL ABSOLUTE TIME
            abs_sec = base_sec + global_start
            h = abs_sec // 3600
            m = (abs_sec % 3600) // 60
            s = abs_sec % 60
            created_at = f"{date_str}T{str(h).zfill(2)}:{str(m).zfill(2)}:{str(s).zfill(2)}.000Z"
            
            # UPDATE DB
            audit = d.get("audit_details", {})
            audit["emotion_stats"] = emo_str
            audit["is_conflict"] = is_conflict
            
            scores = [
                audit.get("cross_sales_score", 0),
                audit.get("upsell_score", 0),
                audit.get("christmas_tree_score", 0),
                audit.get("promo_score", 0),
                audit.get("loyalty_score", 0),
                audit.get("order_duplication_score", 0)
            ]
            avg_score = sum(scores) / 6.0 if not is_conflict else 0
            new_score = round(avg_score / 20.0, 1)
            
            supabase.table("dialogs").update({
                "audio_url": new_audio_url,
                "created_at": created_at,
                "audit_details": audit,
                "score": new_score
            }).eq("id", d_id).execute()
            
            logging.info(f" -> Успех! Ссылка: {new_audio_url}")
            
        except Exception as e:
            logging.error(f"Ошибка при обработке {d_id}: {e}")

if __name__ == '__main__':
    main()
