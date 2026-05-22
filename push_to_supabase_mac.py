import os
import json
import logging
from dotenv import load_dotenv
from supabase import create_client, Client

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# Загружаем .env
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(env_path)

def push_report_to_supabase(json_path: str, shop_id: int = 1, audio_path: str = "", date_folder: str = "", shop_name: str = ""):
    url = os.environ.get("SUPABASE_URL") or os.environ.get("NEXT_PUBLIC_SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE") or os.environ.get("SUPABASE_ANON_KEY")

    if not url or not key:
        logging.error("Не найдены переменные SUPABASE_URL или SUPABASE_ANON_KEY в .env")
        return

    supabase: Client = create_client(url, key)
    file_name = "" # Initialize for scope
    
    if not os.path.exists(json_path):
        logging.error(f"Файл {json_path} не найден!")
        return

    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        logging.error(f"Ошибка при парсинге JSON: {e}")
        return

    if not shop_id:
        logging.warning("shop_id не передан. Будет использован ID: 1")
        shop_id = 1

    public_audio_url = ""
    
    if audio_path and os.path.exists(audio_path):
        file_name = os.path.basename(audio_path)
        
        # Build structured R2 path: shop-name/date/filename.ogg
        safe_shop = (shop_name or "unknown").replace(" ", "-").lower()
        r2_key = f"{safe_shop}/{date_folder}/{file_name}" if date_folder else file_name
        
        # Cloudflare R2 configurations
        r2_access = os.environ.get("R2_ACCESS_KEY")
        r2_secret = os.environ.get("R2_SECRET_KEY")
        r2_account_id = os.environ.get("R2_ACCOUNT_ID")
        r2_bucket = os.environ.get("R2_BUCKET_NAME")
        r2_public_url = os.environ.get("R2_PUBLIC_URL")

        if all([r2_access, r2_secret, r2_account_id, r2_bucket, r2_public_url]):
            import boto3
            try:
                # Initialize Boto3 client for R2
                s3 = boto3.client(
                    service_name='s3',
                    endpoint_url=f'https://{r2_account_id}.r2.cloudflarestorage.com',
                    aws_access_key_id=r2_access,
                    aws_secret_access_key=r2_secret,
                    region_name='auto'
                )
                
                # Upload to R2
                content_type = "audio/ogg" if file_name.lower().endswith(".ogg") else "audio/wav"
                with open(audio_path, "rb") as f:
                    s3.upload_fileobj(f, r2_bucket, r2_key, ExtraArgs={"ContentType": content_type})
                
                public_audio_url = f"{r2_public_url.rstrip('/')}/{r2_key}"
                logging.info(f"Аудио загружено в Cloudflare R2: {public_audio_url}")
            except Exception as e:
                logging.error(f"Ошибка загрузки аудио в R2: {e}")
        else:
            logging.error("Нет нужных переменных R2 в .env")
    else:
        logging.warning("Аудиофайл не передан или не существует. audio_url будет пустым.")

    dialogues = data.get("dialogues", [])
    if not dialogues:
        logging.warning("В JSON нет массива dialogues.")
        return

    import difflib
    recent_dialogs = []
    try:
        recent_res = supabase.table("dialogs").select("clean_text").eq("shop_id", shop_id).order("created_at", desc=True).limit(50).execute()
        if recent_res.data:
            recent_dialogs = [rd.get("clean_text", "") for rd in recent_res.data if rd.get("clean_text")]
    except Exception as e:
        logging.error(f"Ошибка при получении недавних диалогов для дедупликации: {e}")

    for idx, dialog in enumerate(dialogues):
        qa = dialog.get("qa_evaluation", {})
        
        # Считаем средний балл (от 0 до 100)
        scores = [
            qa.get("cross_sales_score", 0),
            qa.get("upsell_score", 0),
            qa.get("christmas_tree_score", 0),
            qa.get("promo_score", 0),
            qa.get("loyalty_score", 0),
            qa.get("order_duplication_score", 0)
        ]
        
        # Если конфликт, то оценка 0
        avg_score = sum(scores) / 6.0 if not qa.get("is_conflict", False) else 0

        # Преобразуем формат transcript
        raw_transcript = dialog.get("transcript", [])
        formatted_transcript = []
        for line in raw_transcript:
            formatted_transcript.append({
                "start": line.get("start", line.get("start_time", 0)),
                "end": line.get("end", line.get("end_time", 0)),
                "speaker": line.get("speaker", line.get("role", "Unknown")),
                "text": line.get("text", "")
            })

        has_wow = qa.get("live_service_score", 0) >= 100

        clean_text_str = " ".join([t["text"] for t in formatted_transcript])
        
        is_duplicate = False
        import re
        def get_words(text):
            return set(re.findall(r'\w+', text.lower()))
            
        words1 = get_words(clean_text_str)
        if len(words1) > 0:
            for rd_text in recent_dialogs:
                words2 = get_words(rd_text)
                if len(words2) > 0:
                    jaccard = len(words1 & words2) / len(words1 | words2)
                    if jaccard > 0.85: # Relaxed from 0.65 to avoid false positives for short phrases
                        is_duplicate = True
                        break
                
        if is_duplicate:
            logging.info(f"Диалог #{idx+1} пропущен (обнаружен дубликат).")
            continue

        safe_file_name = file_name if 'file_name' in locals() else f"dialog_{idx+1}.ogg"

        row = {
            "shop_id": shop_id,
            "dialog_index": idx + 1,
            "original_audio_file": safe_file_name if public_audio_url else f"dialog_{idx+1}.ogg",
            "clean_text": clean_text_str,
            "speakers_involved": list(set([t["speaker"] for t in formatted_transcript])),
            "transcript": formatted_transcript,
            "score": round(avg_score / 20.0, 1), # Scale 0-100 to 0-5 to satisfy DB constraints
            "text_analysis": qa.get("recommendation", ""),
            "audio_url": public_audio_url,
            "audit_details": {
                "dialogue_type": dialog.get("dialogue_type", "standard"),
                "cross_sales_score": qa.get("cross_sales_score") or 0,
                "upsell_score": qa.get("upsell_score") or 0,
                "christmas_tree_score": qa.get("christmas_tree_score") or 0,
                "promo_score": qa.get("promo_score") or 0,
                "loyalty_score": qa.get("loyalty_score") or 0,
                "order_duplication_score": qa.get("order_duplication_score") or 0,
                "live_service_score": qa.get("live_service_score") or 0,
                "additional_service": qa.get("additional_service", ""),
                "critical_errors": qa.get("critical_errors", ""),
                "recommendation": qa.get("recommendation", ""),
                "emotion_stats": qa.get("emotion_stats", ""),
                "is_conflict": qa.get("is_conflict", False)
            }
        }
        
        if date_folder and formatted_transcript:
            # Use the absolute 'start' from the first line of transcript (seconds from midnight)
            abs_start = formatted_transcript[0]["start"]
            h = abs_start // 3600
            m = (abs_start % 3600) // 60
            s = abs_start % 60
            row["created_at"] = f"{date_folder}T{str(h).zfill(2)}:{str(m).zfill(2)}:{str(s).zfill(2)}.000Z"

        try:
            res = supabase.table("dialogs").insert(row).execute()
            logging.info(f"Диалог #{idx+1} успешно отправлен в Supabase!")
        except Exception as e:
            logging.error(f"Ошибка при отправке в Supabase: {e}")

if __name__ == "__main__":
    import sys
    report_file = sys.argv[1] if len(sys.argv) > 1 else 'FINAL_AUDIT_REPORT.json'
    shop_id_arg = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    audio_file = sys.argv[3] if len(sys.argv) > 3 else ''
    push_report_to_supabase(os.path.join(os.path.dirname(__file__), report_file), shop_id=shop_id_arg, audio_path=audio_file)
