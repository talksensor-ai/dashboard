import json
import os
import glob

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

def find_audio_segment_buggy(global_start, global_end, file_shifts):
    if not file_shifts:
        return None, 0, 0
    first_file_shift = file_shifts[0][0]
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

def inspect():
    root_audio_dir = "/Users/ai/talk"
    file_shifts = get_ogg_files(root_audio_dir)
    
    # Let's filter files for date 2026-05-21
    day_shifts = [(shift, fpath) for shift, fpath in file_shifts if "2026-05-21" in os.path.basename(fpath)]
    print(f"Day shifts for 2026-05-21: {len(day_shifts)}")
    for s, fp in day_shifts:
        print(f"  Shift: {s}s ({s//3600:02d}:{(s%3600)//60:02d}) -> {os.path.basename(fp)}")

    with open('/Users/ai/talk/pipeline/results_2026-05-21.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    results = data.get('results', [])
    
    # We will also parse the cumulative canvas to see the ACTUAL chunks
    with open('/Users/ai/talk/daily_canvas_2026-05-21_cumulative.txt', 'r', encoding='utf-8') as f:
        canvas_content = f.read()
    
    # Find all chunks headers
    # e.g., === Файл: 08-56, смещение: 3360с (08:56) ===
    chunks = []
    import re
    pattern = re.compile(r'=== Файл:\s*([^\n,]+),\s*смещение:\s*(\d+)с\s*.*?===')
    for m in pattern.finditer(canvas_content):
        chunks.append({
            "name": m.group(1).strip(),
            "offset": int(m.group(2)),
            "pos": m.start()
        })
        
    print(f"\nCanvas chunks count: {len(chunks)}")
    for c in chunks:
        print(f"  Chunk name: {c['name']}, offset: {c['offset']}s")

    print("\nMapping verification for dialogues:")
    for r in results:
        idx = r.get('idx')
        eval_data = r.get('evaluation', {})
        transcript = eval_data.get('transcript', [])
        starts = [t.get('start') for t in transcript if t.get('start') is not None]
        ends = [t.get('end') for t in transcript if t.get('end') is not None]
        if not starts:
            continue
        g_start = min(starts)
        g_end = max(ends)
        
        # Buggy mapping (as currently implemented in pipeline and regenerate_dialogue_audio.py)
        buggy_file, b_start, b_end = find_audio_segment_buggy(g_start, g_end, day_shifts)
        
        # Let's find which chunk it actually belongs to according to the canvas
        actual_chunk = None
        for i in range(len(chunks)-1, -1, -1):
            if g_start >= chunks[i]["offset"]:
                actual_chunk = chunks[i]
                break
        
        if not actual_chunk:
            actual_chunk = chunks[0]
            
        # Is the buggy file name matching actual chunk name?
        # Buggy file name e.g., "2026-05-21_08-56-21-05-2026.ogg"
        # Actual chunk name e.g., "08-56"
        is_correct_file = actual_chunk["name"] in os.path.basename(buggy_file)
        
        # Calculate actual correct offset
        correct_start = g_start - actual_chunk["offset"]
        correct_end = g_end - actual_chunk["offset"]
        
        # Check if they match
        offsets_match = abs(b_start - correct_start) < 2
        
        if not is_correct_file or not offsets_match:
            print(f"Dialogue #{idx} (time: {g_start}-{g_end}s):")
            print(f"  [BUGGY]  file: {os.path.basename(buggy_file)}, offset: {b_start:.1f}s")
            print(f"  [ACTUAL] chunk: {actual_chunk['name']}, correct offset: {correct_start:.1f}s")
            print(f"  --> MATCH: file={is_correct_file}, offset={offsets_match}")

if __name__ == "__main__":
    inspect()
