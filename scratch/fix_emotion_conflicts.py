import os
import re
import logging
from dotenv import load_dotenv
from supabase import create_client, Client

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(env_path)

url = os.environ.get("SUPABASE_URL") or os.environ.get("NEXT_PUBLIC_SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE") or os.environ.get("SUPABASE_ANON_KEY")
supabase: Client = create_client(url, key)

def main():
    # Fetch all dialogs for 2026-05-21
    res = supabase.table("dialogs").select("id,score,audit_details").eq("shop_id", 8).gte("created_at", "2026-05-21T00:00:00Z").lte("created_at", "2026-05-21T23:59:59Z").execute()
    
    dialogs = res.data
    logging.info(f"Найдено {len(dialogs)} диалогов за 21 мая.")
    
    fixed_count = 0
    
    for d in dialogs:
        audit = d.get("audit_details", {})
        if audit.get("is_conflict") is True:
            emo_stats = audit.get("emotion_stats", "")
            # Example: [ЭМОЦИИ: angry=0.38, neutral=0.50, positive=0.10, sad=0.00] [КОНФЛИКТ]
            m = re.search(r'angry=([\d\.]+)', emo_stats)
            if m:
                angry_val = float(m.group(1))
                if angry_val <= 0.65:
                    # Fix it!
                    logging.info(f"Диалог ID {d['id']} имеет ложный конфликт (angry={angry_val}). Исправляем...")
                    
                    # Remove [КОНФЛИКТ] from emo_stats
                    new_emo_stats = emo_stats.replace("[КОНФЛИКТ]", "").strip()
                    audit["emotion_stats"] = new_emo_stats
                    audit["is_conflict"] = False
                    
                    # Recalculate score
                    scores = [
                        audit.get("cross_sales_score", 0),
                        audit.get("upsell_score", 0),
                        audit.get("christmas_tree_score", 0),
                        audit.get("promo_score", 0),
                        audit.get("loyalty_score", 0),
                        audit.get("order_duplication_score", 0)
                    ]
                    avg_score = sum(scores) / 6.0
                    new_score = round(avg_score / 20.0, 1)
                    
                    # Update DB
                    try:
                        supabase.table("dialogs").update({
                            "audit_details": audit,
                            "score": new_score
                        }).eq("id", d["id"]).execute()
                        fixed_count += 1
                        logging.info(f"  -> ID {d['id']} обновлен. Новый балл: {new_score}")
                    except Exception as e:
                        logging.error(f"Ошибка обновления ID {d['id']}: {e}")
                        
    logging.info(f"Готово! Исправлено ложных конфликтов: {fixed_count}")

if __name__ == '__main__':
    main()
