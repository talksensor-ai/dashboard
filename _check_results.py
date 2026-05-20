import os
from dotenv import load_dotenv
from supabase import create_client
load_dotenv("e:/talk/.env")
sb = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_ROLE"])
res = sb.table("dialogs").select("id, dialog_index, score, audio_url, audit_details, created_at").eq("shop_id", 8).order("created_at").limit(10).execute()
for r in res.data:
    ad = r["audit_details"] or {}
    has_audio = "YES" if r["audio_url"] else "NO"
    cs = ad.get("cross_sales_score", "?")
    up = ad.get("upsell_score", "?")
    tree = ad.get("christmas_tree_score", "?")
    promo = ad.get("promo_score", "?")
    loy = ad.get("loyalty_score", "?")
    dup = ad.get("order_duplication_score", "?")
    live = ad.get("live_service_score", "?")
    conflict = ad.get("is_conflict", "?")
    dtype = ad.get("dialogue_type", "?")
    # Check for OLD field names
    old_greeting = ad.get("greeting_score", None)
    old_order = ad.get("order_taking_score", None)
    print(f"idx={r['dialog_index']} | score={r['score']} | audio={has_audio} | type={dtype}")
    print(f"  cs={cs} up={up} tree={tree} promo={promo} loy={loy} dup={dup} live={live} conflict={conflict}")
    if old_greeting is not None or old_order is not None:
        print(f"  !!! OLD FIELDS DETECTED: greeting={old_greeting}, order_taking={old_order}")
    print(f"  audio_url={r['audio_url'][:80] if r['audio_url'] else 'EMPTY'}")
    print()
print(f"Total: {len(res.data)}")
