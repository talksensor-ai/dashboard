import os
import glob
import tempfile
import warnings
import soundfile as sf
import torchaudio

warnings.filterwarnings("ignore")

# Добавляем Homebrew bin в PATH чтобы ffmpeg находился
os.environ["PATH"] = os.environ.get("PATH", "") + ":/opt/homebrew/bin"

# Кэш модели GigaAM-Emo (загружается один раз)
_emo_model = None

def _get_emo_model():
    global _emo_model
    if _emo_model is None:
        import gigaam
        import torch
        device = "mps" if torch.backends.mps.is_available() else ("cuda" if torch.cuda.is_available() else "cpu")
        print(f"[EMO] Загрузка GigaAM-Emo (устройство: {device})...")
        _emo_model = gigaam.load_model("emo", device=device)
        print("[EMO] GigaAM-Emo загружена!")
    return _emo_model


def get_emotion_score(global_start, global_end, date_folder, root_path="/root/talk/test_compare"):
    """
    Finds the right audio snippet for the global timestamps and gets its emotion probabilities.
    
    global_start: e.g. 52250 (seconds from midnight)
    global_end: e.g. 52270
    date_folder: "2026-04-27"
    root_path: path where the .ogg files are stored locally
    """

    import gigaam
    
    # 1. Find all local .ogg files for this date
    # In reality, they are named e.g., "19-00-27-04-2026.ogg"
    # But daily_cache_worker assumes format 'HH-MM-SS.ogg' or '19-00-27-04-2026.ogg'
    # We'll just look for files in root_path/date_folder or root_path
    
    # For testing on a single file:
    # If the user only gave us 1 file, let's just use it directly.
    # We will build a robust mapping based on the files present.
    
    target_dir = os.path.join(root_path, date_folder)
    if not os.path.exists(target_dir):
        # Fallback to root_path
        target_dir = root_path

    ogg_files = glob.glob(os.path.join(target_dir, "*.ogg"))
    
    if not ogg_files:
        print(f"[EMO] Не найдено .ogg файлов в {target_dir}")
        return {"error": "no audio files"}

    # Calculate shift for each file
    file_shifts = []
    for f in ogg_files:
        basename = os.path.basename(f)
        # Strip date prefix if present (e.g. 2026-04-25_09-00...)
        clean_name = basename
        if '_' in basename:
            clean_name = basename.split('_', 1)[1]
            
        parts = clean_name.split('-')
        try:
            h = int(parts[0])
            m = int(parts[1])
            # In the format HH-MM-DD-MM-YYYY, there are no seconds.
            shift_s = h * 3600 + m * 60
            file_shifts.append((shift_s, f))
        except:
            continue
            
    file_shifts.sort(key=lambda x: x[0])
    
    if not file_shifts:
        # If parsing failed, just use the first file and assume 0 shift
        file_shifts = [(0, ogg_files[0])]

    # Find the right file
    target_file = None
    local_start = global_start
    local_end = global_end
    
    for i in range(len(file_shifts)-1, -1, -1):
        shift, fpath = file_shifts[i]
        if global_start >= shift:
            target_file = fpath
            local_start = global_start - shift
            local_end = global_end - shift
            break
            
    if not target_file:
        target_file = file_shifts[0][1]
        local_start = max(0, global_start - file_shifts[0][0])
        local_end = max(1, global_end - file_shifts[0][0])
        
    print(f"[EMO] Глобальный {global_start}-{global_end} -> Локальный {local_start}-{local_end} в {os.path.basename(target_file)}")
    
    try:
        # Cut audio
        waveform, sr = torchaudio.load(target_file)
        start_idx = int(local_start * sr)
        end_idx = int(local_end * sr)
        
        # Ensure bounds
        start_idx = max(0, min(start_idx, waveform.shape[1] - 1))
        end_idx = max(start_idx + 1, min(end_idx, waveform.shape[1]))
        
        audio_chunk = waveform[:, start_idx:end_idx]
        
        fd, tmp_path = tempfile.mkstemp(suffix=".wav")
        os.close(fd)
        
        sf.write(tmp_path, audio_chunk[0].numpy(), sr)
        
        # Очищаем кэш GPU перед инференсом чтобы избежать OOM на длинных сегментах
        try:
            import torch
            if torch.backends.mps.is_available():
                torch.mps.empty_cache()
        except Exception:
            pass

        # Get emotion (модель кэширована, не перезагружается)
        model = _get_emo_model()
        probs = model.get_probs(tmp_path)
        
        # Return both probs and the path to the cut audio (WAV)
        return probs, tmp_path


        
    except Exception as e:
        print(f"[EMO] Ошибка: {e}")
        return {"error": str(e)}, None

def analyze_emotion_and_tag(global_start, global_end, date_folder, root_path):
    probs, audio_path = get_emotion_score(global_start, global_end, date_folder, root_path)
    if "error" in probs:
        return "[ЭМОЦИИ: ОШИБКА]", False, None
        
    angry = probs.get("angry", 0)
    tag_text = f"[ЭМОЦИИ: angry={angry:.2f}, neutral={probs.get('neutral',0):.2f}, positive={probs.get('positive',0):.2f}, sad={probs.get('sad',0):.2f}]"
    is_conflict = angry > 0.35
    
    if is_conflict:
        tag_text += " [КОНФЛИКТ]"
        
    return tag_text, is_conflict, audio_path
