import json
import os

dump_path = 'e:/talk/scratch/dialogs_dump.json'
with open(dump_path, 'r', encoding='utf-8') as f:
    dialogs = json.load(f)

# Filter by selectedDate '2026-05-21'
date_dialogs = [d for d in dialogs if d.get("created_at", "").startswith("2026-05-21")]

# Group by start timestamp of transcript
groups = {}
for d in date_dialogs:
    transcript = d.get("transcript", [])
    if not transcript:
        continue
    starts = [t.get("start") for t in transcript if t.get("start") is not None]
    if not starts:
        continue
    min_start = min(starts)
    groups.setdefault(min_start, []).append(d)

print(f"Total group timestamps: {len(groups)}")

# Write to comparison_report.txt
report_path = 'e:/talk/scratch/comparison_report.txt'
with open(report_path, 'w', encoding='utf-8') as out:
    out.write("=== QUALITY COMPARISON REPORT: DEEPSEEK PRO VS GEMINI FLASH ===\n")
    out.write(f"Date: 2026-05-21\n")
    out.write(f"Total Dialogues Grouped: {len(groups)}\n\n")
    
    for start_time in sorted(groups.keys()):
        group = groups[start_time]
        out.write(f"Group Start Time: {start_time} seconds from midnight\n")
        out.write("="*100 + "\n")
        
        # Sort group by ID
        group.sort(key=lambda x: x['id'])
        
        for d in group:
            out.write(f"  DB ID: {d['id']} | Score: {d.get('score')} | Created At: {d.get('created_at')}\n")
            out.write(f"  Audio File: {d.get('original_audio_file')}\n")
            out.write(f"  Clean Text: {d.get('clean_text', '').strip()}\n")
            
            audit = d.get('audit_details') or {}
            out.write("  Scores:\n")
            for key in ['cross_sales_score', 'upsell_score', 'christmas_tree_score', 'promo_score', 'loyalty_score', 'order_duplication_score', 'live_service_score']:
                out.write(f"    - {key}: {audit.get(key)}\n")
            
            out.write(f"  Critical Errors: {audit.get('critical_errors')}\n")
            out.write(f"  Recommendation: {audit.get('recommendation')}\n")
            out.write(f"  Text Analysis: {d.get('text_analysis')}\n")
            out.write("-" * 80 + "\n")
        
        out.write("\n" + "="*100 + "\n\n")

print(f"Done! Saved to {report_path}")
