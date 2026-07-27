import os
import json
import logging
from dotenv import load_dotenv
from supabase import create_client, Client

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(env_path)

url = os.environ.get("SUPABASE_URL") or os.environ.get("NEXT_PUBLIC_SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE") or os.environ.get("SUPABASE_ANON_KEY")
supabase: Client = create_client(url, key)

MISSING_INDICES = [39, 40, 50, 51, 55, 62, 66, 67, 77, 80]
JSON_PATH = os.path.join(os.path.dirname(__file__), 'results_2026-05-21_mac.json')

def main():
    with open(JSON_PATH, 'r', encoding='utf-16') as f:
        data = json.load(f)
        
    results = data.get("results", [])
    
    for item in results:
        idx = item.get("idx")
        if idx in MISSING_INDICES:
            dialog = item.get("evaluation", {})
            qa = dialog.get("qa_evaluation", {})
            
            scores = [
                qa.get("cross_sales_score", 0),
                qa.get("upsell_score", 0),
                qa.get("christmas_tree_score", 0),
                qa.get("promo_score", 0),
                qa.get("loyalty_score", 0),
                qa.get("order_duplication_score", 0)
            ]
            avg_score = sum(scores) / 6.0 if not qa.get("is_conflict", False) else 0

            raw_transcript = dialog.get("transcript", [])
            formatted_transcript = []
            for line in raw_transcript:
                formatted_transcript.append({
                    "start": line.get("start", line.get("start_time", 0)),
                    "end": line.get("end", line.get("end_time", 0)),
                    "speaker": line.get("speaker", line.get("role", "Unknown")),
                    "text": line.get("text", "")
                })

            clean_text_str = " ".join([t["text"] for t in formatted_transcript])
            
            row = {
                "shop_id": 8,
                "dialog_index": idx,
                "original_audio_file": f"dialog_{idx}.ogg",
                "clean_text": clean_text_str,
                "speakers_involved": list(set([t["speaker"] for t in formatted_transcript])),
                "transcript": formatted_transcript,
                "score": round(avg_score / 20.0, 1),
                "text_analysis": qa.get("recommendation", ""),
                "audio_url": "", # We will patch this in the next step
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
            
            if formatted_transcript:
                abs_start = formatted_transcript[0]["start"]
                h = abs_start // 3600
                m = (abs_start % 3600) // 60
                s = abs_start % 60
                row["created_at"] = f"2026-05-21T{str(h).zfill(2)}:{str(m).zfill(2)}:{str(s).zfill(2)}.000Z"
            
            # Check if it already exists to be safe
            check = supabase.table("dialogs").select("id").eq("shop_id", 8).eq("dialog_index", idx).gte("created_at", "2026-05-21T00:00:00Z").lte("created_at", "2026-05-21T23:59:59Z").execute()
            if len(check.data) == 0:
                try:
                    res = supabase.table("dialogs").insert(row).execute()
                    logging.info(f"Вставлен диалог #{idx}")
                except Exception as e:
                    logging.error(f"Ошибка вставки #{idx}: {e}")
            else:
                logging.info(f"Диалог #{idx} уже в базе.")

if __name__ == '__main__':
    main()
