import os
import glob
import torchaudio

target_dir = "/Users/ai/talk"
date_folder = "2026-05-21"

ogg_files = glob.glob(os.path.join(target_dir, f"{date_folder}_*.ogg"))
if not ogg_files:
    ogg_files = glob.glob(os.path.join(target_dir, "*.ogg"))

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

if not file_shifts:
    print("No files found!")
    exit()

base_shift = file_shifts[0][0]
print(f"Base shift (first file time): {base_shift}s ({base_shift//3600:02d}:{(base_shift%3600)//60:02d})")

for shift, f in file_shifts:
    try:
        info = torchaudio.info(f)
        duration = info.num_frames / info.sample_rate
    except Exception as e:
        duration = -1
    norm_shift = shift - base_shift
    print(f"File: {os.path.basename(f)}")
    print(f"  Parsed shift: {shift}s | Norm shift: {norm_shift}s")
    print(f"  Actual duration: {duration:.2f}s (~{duration/60:.2f}m)")
    print(f"  Expected end shift: {norm_shift + duration:.2f}s")
